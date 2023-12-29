import sys
import time

from shutil import get_terminal_size

default_color = '\033[1m\033[38;5;34m\033[48;5;0m'

#Custom progress bar
class ProgressBar():

	def __init__(self, iterable, message_length = None, disp = True, freq = 1, color = None):

		if message_length is None:
			message_length = get_terminal_size()[0]

		if color is None:
			color = default_color

		self.iterable = iterable
		self.total = len(iterable)
		self.message_length = message_length
		self.disp = disp
		self.freq = freq
		self.color = color
		
		if self.disp:
			self.update=self.Update
		else:
			self.update=self.Update_Null

	def __iter__(self):

		return PBIterator(self)

	def Update_Null(self, current, rt):

		pass

	def Update(self, current, rt):

		percent = float(current - 1) * 100 / self.total
		itps = current / rt
		projrem = max([0, (self.total - current) / itps])

		str_0 = f"\r{self.color} "
		str_1 = "Progress"
		str_3 = f" ({current-1}/{self.total}) {percent:.2f}%,"
		str_4 = f" {itps:.2f} it/s,"
		str_5 = f" {rt:.2f} s elapsed, {projrem:.2f} s remaining"
		str_6 = "\033[0m\r"

		columns_used = len(str_1 + str_3 + str_4 + str_5)

		bar_length = self.message_length - columns_used

		arrow='-'*int(percent/100*bar_length-1)+'>'
		spaces=' '*(bar_length-len(arrow))

		str_2 = f" [{arrow}{spaces}]"

		message = str_0 + str_1 + str_2 + str_3 + str_4 + str_5 + str_6

		sys.stdout.write(message)
		sys.stdout.flush()

#Custom iterator for progress bar
class PBIterator():
	def __init__(self,ProgressBar):

		self.ProgressBar=ProgressBar
		self.index=0
		self.rt=0
		self.t0=time.time()

	def __next__(self):

		if self.index<len(self.ProgressBar.iterable):

			self.index+=1
			self.rt=time.time()-self.t0

			if self.index%self.ProgressBar.freq==0:
				self.ProgressBar.update(self.index,self.rt)

			return self.ProgressBar.iterable[self.index-1]

		else:

			self.index+=1
			self.rt=time.time()-self.t0

			self.ProgressBar.update(self.index,self.rt)

			if self.ProgressBar.disp:
				
				print('\n')

			raise StopIteration