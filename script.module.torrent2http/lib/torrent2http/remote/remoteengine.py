from ..engine import Engine
from ..error import Error
from ..util import ensure_fs_encoding

import filesystem, log
import json, base64, urllib, os, time

try:
	import requests
except ImportError:
	import sys, xbmc
	req_path = os.path.join(xbmc.translatePath("special://home/addons"), "script.module.requests","lib")
	if os.path.exists(req_path):
		sys.path.append(req_path)
		import requests

class RemoteProcess:

	def __init__(self, client_engine):
		self.engine = client_engine

	def poll(self):
		url = "http://%s:%d/poll" % (self.engine.settings.remote_host, self.engine.settings.remote_port)
		log.debug(url)
		r = requests.get(url, params={'pid': self.engine.process.pid})
		
		if r.status_code == requests.codes.ok:
			if r.text == 'None':
				return None
			
			return r.text
		else:
			return None

	def wait(self, timeout=None):
		url = "http://%s:%d/wait" % (self.engine.settings.remote_host, self.engine.settings.remote_port)
		log.debug(url)
		r = requests.get(url, params={'pid': self.engine.process.pid})
		
		if r.status_code == requests.codes.ok:
			return int(r.text)
		else:
			return 0

	def terminate(self):
		url = "http://%s:%d/terminate" % (self.engine.settings.remote_host, self.engine.settings.remote_port)
		log.debug(url)
		requests.get(url, params={'pid': self.engine.process.pid})

	def kill(self):
		url = "http://%s:%d/kill" % (self.engine.settings.remote_host, self.engine.settings.remote_port)
		log.debug(url)
		requests.get(url, params={'pid': self.engine.process.pid})

		
class ClientEngine(Engine):

	def __init__(self, *args, **kwargs):
		from remotesettings import Settings
		self.settings = Settings()

		kwargs['bind_host'] = self.settings.remote_host

		Engine.__init__(self, *args, **kwargs)
		
		arg_names = ['uri', 'binaries_path', 'platform', 'download_path',
                 'bind_host', 'bind_port', 'connections_limit', 'download_kbps', 'upload_kbps',
                 'enable_dht', 'enable_lsd', 'enable_natpmp', 'enable_upnp', 'enable_scrape',
                 'log_stats', 'encryption', 'keep_complete', 'keep_incomplete',
                 'keep_files', 'log_files_progress', 'log_overall_progress', 'log_pieces_progress',
                 'listen_port', 'use_random_port', 'max_idle_timeout', 'no_sparse', 'resume_file',
                 'user_agent', 'startup_timeout', 'state_file', 'enable_utp', 'enable_tcp',
                 'debug_alerts', 'logger', 'torrent_connect_boost', 'connection_speed',
                 'peer_connect_timeout', 'request_timeout', 'min_reconnect_time', 'max_failcount',
                 'dht_routers', 'trackers']
			
		i = 0
		for arg in args:
			kwargs[arg_names[i]] = arg
			i += 1
		
		self.sobj = ClientEngine.toJSON(kwargs)

	@staticmethod
	def _torrent_data_by_url(url):
		path = urllib.url2pathname(url.replace('file:', '')).decode('utf-8')
		if filesystem.exists(path):
			with filesystem.fopen(path, 'rb') as t:
				return t.read()
		return None

	@staticmethod
	def toJSON(o):
		return json.dumps(o)

	def MyPopen(self, args, **kwargs):
		for i in args[1:]:
			print i

		o = {"jsonrpc": "2.0", "method": "Addons.ExecuteAddon", "id": "2"}

		tdata = ''
		if self.uri.startswith('file:'):
			tdata = ClientEngine._torrent_data_by_url(self.uri)
			tdata = base64.b64encode(tdata)

		args_str = json.dumps(args[1:])
		args_str = base64.b64encode(args_str)
		dict_str = self.sobj
		dict_str = base64.b64encode(dict_str)


		params = {"addonid":"script.module.torrent2http.remote", "params": {"args": args_str, 'torrent_data': tdata, "dict": dict_str }}
		o['params'] = params

		print o

		url = "http://%s:%d/popen" % (self.settings.remote_host, self.settings.remote_port)
		try:
			r = requests.post(url, data={"args": args_str, 'torrent_data': tdata, "dict": dict_str})
			if r.text == 'None':
				return None
				
			parts = r.text.split('.') 
			
			if len(parts) > 1:
				self.bind_port = int(parts[1])
				log.debug('Bind port from server: %d' % self.bind_port)
	
			pid = int(parts[0])
			proc = RemoteProcess(self)
			proc.pid = pid
			
			
			return proc
			
		except requests.exceptions.RequestException as e:
			print e
			
		return None

	def _get_binary_path(self, binaries_path):
		return "torrent2http"
		
	def _log(self, message):
		log.debug(message)

	@staticmethod
	def _validate_save_path(path):
		return path

	def can_bind(self, host, port):
		url = "http://%s:%d/can_bind" % (self.settings.remote_host, self.settings.remote_port)
		try:
			r = requests.post(url, data={"host": host, 'port': port})
			if r.status_code == requests.codes.ok:
				log.debug(r)
				return r.text == 'True'
		except requests.exceptions.RequestException as e:
			print e
		return False

	def find_free_port(self, host):
		url = "http://%s:%d/find_free_port" % (self.settings.remote_host, self.settings.remote_port)
		try:
			r = requests.post(url, data={"host": host})
			if r.status_code == requests.codes.ok:
				log.debug(r)
				return int(r.text)
		except requests.exceptions.RequestException as e:
			print e
		return False

	def file_status(self, file_index, timeout=10):
		fs = Engine.file_status(self, file_index, timeout)

		from torrent2http import FileStatus
		
		try:
			url = None
			if fs.url:
				import urlparse, re
				res = urlparse.urlparse(fs.url)
				port = re.search(r':(\d+)', res.netloc).group(1)

				res = urlparse.ParseResult(res.scheme, 
											'%s:%s' % (self.settings.remote_host, port), 
											res.path, res.params, res.query, res.fragment)
				url=urlparse.urlunparse(res)

			return FileStatus(index=fs.index, name=fs.name, save_path=fs.save_path, url=url,
		                  size=fs.size, offset=fs.offset, download=fs.download, progress=fs.progress, media_type=fs.media_type)
		except:
			return None

	def start(self, start_index=None):
		'''
		if not self.can_bind(self.bind_host, self.bind_port):
			port = self.find_free_port(self.bind_host)
			if port is False:
				raise Error("Can't find port to bind torrent2http", Error.BIND_ERROR)
			self._log("Can't bind to %s:%s, so we found another port: %d" % (self.bind_host, self.bind_port, port))
			self.bind_port = port
		'''
			
		kwargs = {
			'--bind': "%s:%s" % (self.bind_host, self.bind_port),
			'--uri': self.uri,
			'--file-index': start_index,
			#'--dl-path': download_path,
			'--connections-limit': self.connections_limit,
			'--dl-rate': self.download_kbps,
			'--ul-rate': self.upload_kbps,
			'--enable-dht': self.enable_dht,
			'--enable-lsd': self.enable_lsd,
			'--enable-natpmp': self.enable_natpmp,
			'--enable-upnp': self.enable_upnp,
			'--enable-scrape': self.enable_scrape,
			'--encryption': self.encryption,
			'--show-stats': self.log_stats,
			'--files-progress': self.log_files_progress,
			'--overall-progress': self.log_overall_progress,
			'--pieces-progress': self.log_pieces_progress,
			'--listen-port': self.listen_port,
			'--random-port': self.use_random_port,
			'--keep-complete': self.keep_complete,
			'--keep-incomplete': self.keep_incomplete,
			'--keep-files': self.keep_files,
			'--max-idle': self.max_idle_timeout,
			'--no-sparse': self.no_sparse,
			'--resume-file': self.resume_file,
			'--user-agent': self.user_agent,
			'--state-file': self.state_file,
			'--enable-utp': self.enable_utp,
			'--enable-tcp': self.enable_tcp,
			'--debug-alerts': self.debug_alerts,
			'--torrent-connect-boost': self.torrent_connect_boost,
			'--connection-speed': self.connection_speed,
			'--peer-connect-timeout': self.peer_connect_timeout,
			'--request-timeout': self.request_timeout,
			'--min-reconnect-time': self.min_reconnect_time,
			'--max-failcount': self.max_failcount,
			'--dht-routers': ",".join(self.dht_routers),
			'--trackers': ",".join(self.trackers),
		}

		args = []
		for k, v in kwargs.iteritems():
			if v is not None:
				if isinstance(v, bool):
					if v:
						args.append(k)
					else:
						args.append("%s=false" % k)
				else:
					args.append(k)
					if isinstance(v, str) or isinstance(v, unicode):
						v = ensure_fs_encoding(v)
					else:
						v = str(v)
					args.append(v)

		self._log("Invoking %s" % " ".join(args))
		try:
			self.process = self.MyPopen(args)
		except OSError, e:
			raise Error("Can't start torrent2http: %r" % e, Error.POPEN_ERROR)

		start = time.time()
		self.started = True
		initialized = False
		while (time.time() - start) < self.startup_timeout:
			time.sleep(0.1)
			if not self.is_alive():
				raise Error("Can't start torrent2http, see log for details", Error.PROCESS_ERROR)
			try:
				self.status(1)
				initialized = True
				break
			except Error:
				pass

		if not initialized:
			self.started = False
			raise Error("Can't start torrent2http, time is out", Error.TIMEOUT)
		self._log("torrent2http successfully started.")
		
	def close(self):
		url = None
		pid = None
		if self.process:
			url = "http://%s:%d/close" % (self.settings.remote_host, self.settings.remote_port)
			pid = self.process.pid
			
		Engine.close(self)
		
		if url and pid:
			requests.get(url, params={'pid': pid})

			
class ServerEngine(Engine):
	def __init__(self, **kwargs):
		from remotesettings import Settings
		self.settings = Settings()

		if 'resume_file' in kwargs:
			resume_path = filesystem.join(self.settings.storage_path, '.resume')
			if not filesystem.exists(resume_path):
				filesystem.makedirs(resume_path)
			resume_name = filesystem.basename(kwargs['resume_file'])
			resume_name = resume_name.split('\\')[-1]
			kwargs['resume_file'] = filesystem.join(resume_path, resume_name)
			log.debug('resume_file is: ' + kwargs['resume_file'])

		kwargs['bind_host'] = self.settings.remote_host
		Engine.__init__(self, **kwargs)

	'''
	def can_bind(self, host, port):
		return True
	'''

	def pid(self):
		try:
			return self.process.pid
		except:
			return None

if __name__ == '__main__':
	import sys

	if len(sys.argv) > 2:
		print sys.argv[2]
