#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  JobScraper.py
#  
#  Copyright 2017 Emma Davenport <davenport.physics@gmail.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  
from urllib.request import urlopen
from threading import Thread


'''

	Careerbuilder is very easy to predict job search related url's.
	
	What I do notice is that there are typically not emails associated with
	a position, but that maybe linkedln might be a valueable asset in this
	regard. Hiring managers for a particular place will more than likely have
	their own linkedln page, where their email will more than
	likely be located.

'''

def main(args):
	
	Jobs = JobSearchWithCareerBuilder("entry-software", Location = "", KeyWords=("C++").split())
	
	return 0


class JobSearchWithCareerBuilder(object):
	
	'''
	
		Opens URL decerned from Job Name and Location. It also determines
		how many pages were found with basic job name.
	
	'''
	def __init__(self,JobName,Location="",KeyWords=[]):
		
		self.KeyWords = KeyWords
		self.RawHTMLPages = []
		self.RawHTMLPages.append( urlopen("https://www.careerbuilder.com/jobs-" + JobName + Location).read() )
		
		self.DeterminePageCount()
		
		try:
			
			def RawHTMLPagesWorker(string):
				self.RawHTMLPages.append(urlopen(string).read())
				
			
			for i in range(2, self.PageCount+1):
				Thread(target=RawHTMLPagesWorker, args=("https://www.careerbuilder.com/jobs-" + JobName + Location + "?page_number=" + str(i),)).start()
				#self.RawHTMLPages.append(urlopen("https://www.careerbuilder.com/jobs-" + JobName + Location + "?page_number=" + str(i)).read())
		except: pass
		
		self.ParseJobLinksFromHTML()
		self.VisitJobSites()
		self.ParseDescriptions()
		
	def DeterminePageCount(self):
		
		html = str(self.RawHTMLPages[0]).split("\\n")
		
		for line in html:
			if "Page 1 of" in line:
				self.PageCount = int(line.split(" ")[-1])
		
	def ParseJobLinksFromHTML(self):
		
		self.JobLinks = []
		
		for html in self.RawHTMLPages:
			parsehtml = str(html).split()
			for line in parsehtml:
				if "href=" in line and "job" in line:
					if "careerbuilder" in line or "saved-jobs" in line or "jobs" in line:
						continue
					else:
						line = line[6:-1]
						qoutation = line.find("\"")
						line = line[:qoutation]
						self.JobLinks.append(line)
						
	def VisitJobSites(self):
		
		self.Jobs = []
		
		def job_worker(string):
			self.Jobs.append(str(urlopen(string).read()))
		
		for job in self.JobLinks:
			#print("https://www.careerbuilder.com" + job)
			Thread(target=job_worker,args=("https://www.careerbuilder.com" + job,))
			#self.Jobs.append(str(urlopen("https://www.careerbuilder.com" + job).read()))
			
	def ParseDescriptions(self):
		
		fp = open("Links", "w")
		for Job in self.Jobs:
			HowManyKeyWordsFound = 0
			for Keyword in self.KeyWords:
				if KeyWord in Job:
					HowManyKeyWordsFound += 1
			if HowManyKeyWordsFound == len(self.KeyWords):
				fp.writeln(Job)
				
		fp.close()

if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))
