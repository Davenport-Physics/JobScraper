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


'''

	Careerbuilder is very easy to predict job search related url's.
	
	What I do notice is that there are typically not emails associated with
	a position, but that maybe linkedln might be a valueable asset in this
	regard. Hiring managers for a particular place will more than likely have
	their own linkedln page, where their email will more than
	likely be located.

'''

def main(args):
	
	Jobs = JobSearchWithCareerBuilder("entry-software", Location = "dallas,tx", KeyWords=("C++ Java Python Programming  Physics Mathematics").split())
	
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
			for i in range(2, self.PageCount+1):
				self.RawHTMLPages.append(urlopen("https://www.careerbuilder.com/jobs-" + JobName + Location + "?page_number=" + str(i)).read())
		except: pass
		
		self.ParseJobLinksFromHTML()
		self.VisitJobSites()
		
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
						self.JobLinks.append(line[6:-7])
						
	def VisitJobSites(self):
		
		self.Jobs = []
		
		for job in self.JobLinks
			self.Jobs.append(str(urlopen("https://www.careerbuilder.com" + job).read()))
			
	def ParseDescriptions(self):
		
		for KeyWord in self.KeyWords:
			for Job in self.Jobs:
				continue #Stopped right here

if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))
