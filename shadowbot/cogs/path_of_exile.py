import discord
from discord.ext import commands
from cogs import Cog
import io
import concurrent.futures
from messages.bot_messages import DeletableMessage, PagedMessage
import aiohttp
import re
import base64
import zlib
from defusedxml.cElementTree import fromstring as xmlfromstring
import poe
from collections import OrderedDict


# https://gist.github.com/BananaWagon/068cef8ff640e90d3636d133fa8f72a1
class POECog(Cog):
	""" Path of Exile Module """
	def __init__(self, bot):
		super().__init__(bot)

	def build_item_image(self, term):
		poe_client = poe.client.Client()
		item = poe_client.find_items(where={
			'name': '%' + str(term) + '%',
			'rarity': 'Unique'
		}, limit=1)
		if not item:
			return None
		item = item[0]
		print(item)
		# noinspection PyUnresolvedReferences
		rend = poe.utils.ItemRender(item.rarity)
		img = rend.render(item)
		buf = io.BytesIO()
		img.save(buf, 'PNG')
		return buf.getvalue()

	@commands.command()
	async def poe(self, ctx: commands.context.Context, item_name):
		"""Look up a PoE Unique.
		Returns an image. "/poe starforge """
		with ctx.typing():
			# 3. Run in a custom process pool:
			with concurrent.futures.ThreadPoolExecutor() as pool:
				img_bytes = await self.bot.loop.run_in_executor(
					pool, self.build_item_image, item_name)
				msg = DeletableMessage(sql_session=self.sql)
				if not img_bytes:
					await msg.send(ctx, content="Could not find any matching items!")
					return
				await msg.send(ctx, file=discord.File(io.BytesIO(img_bytes),  '%s.png' % item_name))

	# noinspection PyBroadException
	@commands.Cog.listener()
	@commands.guild_only()
	async def on_message(self, message: discord.Message):
		if message.author.bot or not message.guild:
			return
		if 'pastebin.com/' not in message.clean_content:
			return
		url = message.clean_content.split('pastebin.com/')[1].replace('\n', ' ').split(' ')[0]
		xml, raw_url = await self.read_pastebin(url)
		if not xml:
			return  # Invalid poB link.
		with message.channel.typing():
			with concurrent.futures.ThreadPoolExecutor() as pool:
				page_dict = await self.bot.loop.run_in_executor(
					pool, self.parse_pob, xml)
				msg = PagedMessage(sql_session=self.sql, dict_data=page_dict, content="**PoB Link Parser**\n %s" % raw_url)
				await msg.send(message.channel)

	async def read_pastebin(self, url):
		# noinspection PyBroadException
		try:
			url = url
			pb = PasteBin()
			return await pb.load_xml(url), pb.raw_url
		except Exception:
			return None, None  # Not a valid PoB pastebin

	# noinspection PyUnresolvedReferences
	def parse_pob(self, xml):
		""" Builds a dict, ready to be sent as a PagedMessage. Returns None if not valid. """
		# noinspection PyBroadException
		try:
			tree = xmlfromstring(xml)
			parsed = poe.utils.parse_pob_xml(xml, cl=poe.Client())
		except Exception:
			return None  # Not a valid POE Pastebin.
		p = PoeParser(parsed, tree)
		return p.make_output()


# noinspection PyUnresolvedReferences
class PasteBin:
	def __init__(self):
		self.raw_url = None

	async def fetch(self, url):
		async with aiohttp.ClientSession() as session:
			async with session.get(url) as response:
				return await response.text()

	def decode_base64_and_inflate(self, b64string):
		decoded_data = base64.b64decode(b64string)
		try:
			return zlib.decompress(decoded_data)
		except zlib.error:
			pass

	def strip_url_to_key(self, url):
		match = re.search('\w+$', url)
		paste_key = match.group(0)
		return paste_key

	def decode_to_xml(self, enc):
		enc = enc.replace("-", "+").replace("_", "/")
		xml_str = self.decode_base64_and_inflate(enc)
		return xml_str.decode()

	async def get_as_xml(self, paste_key):
		self.raw_url = 'https://pastebin.com/raw/' + paste_key
		# noinspection PyBroadException
		try:
			contents = await self.fetch(self.raw_url)
		except Exception:
			return None

		return self.decode_to_xml(contents)

	async def load_xml(self, pb_url):
		""" Parse the given URL & return the raw XML string. """
		key = self.strip_url_to_key(pb_url)
		return await self.get_as_xml(key)


class PoeParser:
	def __init__(self, json, xml_tree):
		self.json = json
		self.tree = xml_tree

	def get(self, stat, default=None, xml_attrib='value', xml_prop="stat", raw_num=False):
		xmls = self._get_xml(stat, attrib=xml_attrib, raw_num=raw_num, prop=xml_prop)
		if xmls is not None:
			return xmls
		sp = stat.split('.')
		curr_j = self.json
		for s in sp:
			if s in curr_j:
				curr_j = curr_j[s]
			else:
				return default if not raw_num else 0
		# noinspection PyBroadException
		try:
			ret = '{0:,g}'.format(round(float(curr_j), 2))
			if raw_num:
				ret = float(ret)
			return ret
		except Exception:
			pass
		return curr_j

	def _get_xml(self, stat, attrib=None, raw_num=False, prop="stat"):
		# noinspection PyBroadException
		try:
			val = self.tree.find('.//*[@%s="%s"]' % (prop, stat))
			if attrib:
				val = val.attrib[attrib]
			try:
				val = '{0:,g}'.format(round(float(val), 2))
				if raw_num:
					val = float(val)
			except ValueError:
				pass
			return val
		except Exception:
			return None

	def _xml(self, pattern):
		return self.tree.findall(pattern)

	def _build_skills(self):
		""" Returns a list all Skill groups, with the primary first. """
		# noinspection PyBroadException
		groups = []
		try:
			base = self._xml('.//Build')[0]
			main_idx = int(base.attrib['mainSocketGroup']) - 1
			for idx, group in enumerate(self._xml('.//Skill')):
				if 'Swap' in group.attrib['slot']:
					continue
				main_group = sorted(group, key=lambda x: 'gemId' in x and 'Support' in x.attrib['gemId'])
				names = [n.attrib['nameSpec'] for n in main_group]
				names = list(filter(lambda x: not any(e in x.lower() for e in ['edict', 'command of', 'decree of']), names))
				if idx == main_idx:
					groups.insert(0, names)
				else:
					groups.append(names)
		except Exception as ex:
			print(ex)
			pass
		groups = list(filter(lambda g: len(g), groups))
		ret = {}
		for idx, gr in enumerate(groups):
			name = 'Active' if idx == 0 else ('%s-Link' % len(gr))
			ret[name] = ', '.join(gr)
		return ret

	def _build_stats(self):
		""" Returns a dict of Character stats """
		ch = OrderedDict()  # '**__CHARACTER:__**\n'
		ch['Ascendancy'] = self.get('ascendancy')
		ch['Level'] = self.get('level')
		ch['Stats'] = '(Str: %s), (Dex: %s), (Int: %s)' % (self.get('str'), self.get('dex'), self.get('int'))
		ch['Ascendancy'] = self.get('ascendancy')
		ch['Ascendancy Nodes'] = ', '.join(filter(lambda x: ',' not in x, self.get('asc_nodes')))
		ch['keystones'] = ', '.join(self.get('keystones'))
		ch['bandit taken'] = self.get('bandit')
		return ch

	def _build_combat(self):
		ch = OrderedDict()
		ch['total dps'] = self.get('total_dps')
		ch['effective crit chance'] = '%s%%' % self.get('effective_crit_chance')
		ch['chance to hit'] = '%s%%' % self.get('chance_to_hit')
		ch['Life'] = '%s (%s%%)' % (self.get('LifeUnreserved'), self.get('Spec:LifeInc'))
		if self.get('NetLifeRegen', raw_num=True) > 0:
			ch['Net Life Regen'] = self.get('NetLifeRegen')
		ch['Energy Shield'] = '%s (%s%% increased)' % (self.get('es'), self.get('Spec:EnergyShieldInc'))
		if self.get('EnergyShieldRegen', raw_num=True) > 0:
			ch['Net ES Regen'] = self.get('EnergyShieldRegen', raw_num=True) - self.get('degen', raw_num=True)
		ch['Armor'] = '%s (%s%%)' % (self.get('Armour'), self.get('Spec:ArmourInc'))
		ch['Evasion'] = '%s (%s%% increased)' % (self.get('evasion'), self.get('Spec:EvasionInc'))
		ch['Resists'] = ', '.join(['(%s: %s%%)' % (r, self.get(r+'_res')) for r in ['cold', 'fire', 'light', 'chaos']])
		if any(int(x) > 0 for x in [self.get('spell_dodge'), self.get('dodge')]):
			ch['Dodge'] = "(Attack: %s), (Spell: %s)" % (self.get('dodge'), self.get('spell_dodge'))
		if any(int(x) > 0 for x in [self.get('spell_block'), self.get('block')]):
			ch['Block'] = "(Attack: %s), (Spell: %s)" % (self.get('block'), self.get('spell_block'))
		ch['charges'] = ', '.join(['(%s: %s)' % (r, self.get(r+'_charges')) for r in ['endurance', 'frenzy', 'power']])
		return ch

	def _build_gear(self):
		ch = OrderedDict()
		ch['unique jewels'] = ', '.join([j['name'] for j in self.get('jewels')])
		for slot, arr in self.json['equipped'].items():
			if 'swap' in slot.lower():
				continue
			name = arr['parsed']['name']
			if arr['parsed']['rarity'].lower() != 'unique':
				name = '%s (%s)' % (arr['parsed']['base'], arr['parsed']['rarity'])
			ch[slot] = name
		return {k: ch[k] for k in sorted(ch.keys(), key=lambda x: 'z' if 'flask' in x.lower() else x)}

	def _build_config(self):
		ch = OrderedDict()
		for config in self._xml('.//Config'):
			for inp in config:
				attr = inp.attrib
				if 'name' in attr:
					name = attr['name']
					matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', name)  # camelCase.
					# noinspection PyTypeChecker
					name = (' '.join(m.group(0) for m in matches)) \
						.lower() \
						.replace('use ', 'max ') \
						.replace('condition', '') \
						.strip() \
						.title()
					val = [attr[a] for a in attr if a in ('boolean', 'string', 'number')][0]
					ch[name] = str(val).title()
		return {k: ch[k] for k in sorted(ch.keys())}

	def _make_page_content(self, title, d):
		out = {'title': title, 'fields': []}
		if not d:
			out['fields'].append({'name': 'No Config:', 'value': "try adjusting these in PoB"})
		for k, v in d.items():
			out['fields'].append({'name': str(k).title() + ':', 'value': str(v), 'inline': False})
		return out

	def make_output(self):
		return {
			'📝': self._make_page_content('Stats', self._build_stats()),
			'💎': self._make_page_content('Skills', self._build_skills()),
			'⚔': self._make_page_content('Combat', self._build_combat()),
			'👚': self._make_page_content('Gear', self._build_gear()),
			'⚙': self._make_page_content('Config', self._build_config()),
		}


# When we load the cog, we use the name of the file.
def setup(bot):
	# TODO: Add this to all setups.
	cog = POECog(bot)
	cog.settings.register('enabled', True)
	if cog.settings.get('enabled'):
		bot.add_cog(cog)
