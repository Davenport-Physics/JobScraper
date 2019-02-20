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
from time import sleep

import sqlite3
import os.path
import sys
import traceback


'''

    Careerbuilder is very easy to predict job search related url's.
    
    What I do notice is that there are typically not emails associated with
    a position, but that maybe linkedln might be a valueable asset in this
    regard. Hiring managers for a particular place will more than likely have
    their own linkedln page, where their email will more than
    likely be located.

'''

def main(args):
    
    KeyWords, Locations, JobTitles = GetKeyWordsLocationsAndJobTitlesFromFile()

    for job in JobTitles:
        for Location in Locations:
            JobSearchWithCareerBuilder(job, Location = Location, KeyWords=KeyWords)
    
    return 0

def GetKeyWordsLocationsAndJobTitlesFromFile():

    fp   = open("info", "r")
    file_info = []
    for line in fp:
        file_info.append(line)
    fp.close()

    return file_info[0].split(), file_info[1].split(), file_info[2].split()

    
def CombineWrittenFilesByLocation(Locations, JobTitles):
    
    for location in Locations:
        fp = open("combined-" + location + ".tsv", "w")
        jobs = []
        for job in JobTitles:
            if len(location) > 0:
                location = "-in-" + location + "?location="
            ReadLocationJobFile(location+job+".tsv")
            
        fp.close()

class JobSearchWithCareerBuilder(object):
    
    '''
    
        Opens URL decerned from Job Name and Location. It also determines
        how many pages were found with basic job name.
    
    '''
    def __init__(self,JobName,Location="",KeyWords=[]):
        
        self.JobName = JobName
        self.Location = Location
        self.KeyWords = KeyWords
        self.RawHTMLPages = []

        self.connection = None
        self.executor = None

        self.OpenDBConnection()
        
        '''
        
            If the user passed a location, we have to modify the data
            they gave us to fit into careerbuilder's standard url practices.
        
        '''
        if len(Location) > 0:
            Location = "-in-" + Location + "?location="
        
        '''
        
            Opens up the first page that can be discerned by the job name and
            location information. Immediately determines how many pages were found.
        
        '''
        self.RawHTMLPages.append( urlopen("https://www.careerbuilder.com/jobs-" + JobName + Location).read() )
        self.DeterminePageCount()
        
        '''
        
            Local function used for threading. Simple opens up urls and
            adds them to the RawHTMLPages array.
        
        '''
        def RawHTMLPagesWorker(string, SecondAttempt=False):
                
            try:
                self.RawHTMLPages.append(urlopen(string,timeout=5).read())
            except:
                if SecondAttempt is False:
                    sleep(1.0)
                    RawHTMLPagesWorker(string, SecondAttempt=True)
        '''
        
            From the page count that was determined, we make an equivalent
            amount of threads. Each of the threads will open up a page and
            simple store the information provided into the RawHTMLPages array.
        
        '''
        Threads = []
        for i in range(2, self.PageCount+1):
            Threads.append(Thread(target=RawHTMLPagesWorker, args=("https://www.careerbuilder.com/jobs-" + JobName + Location + "?page_number=" + str(i),)))
            
        for thread in Threads:
            thread.start()
            sleep(0.025)
        for thread in Threads:
            thread.join()
            
        '''
        
            From RawHTMLPages, we attempt to parse the job listing links
            that can be found. All of the links are placed into an array
            called JobLinks
        
        '''
            
        self.ParseJobLinksFromHTML()
        
        '''
        
            Once we've obtained every link for every job listing, we
            then visit each website. Each website has a Job Description
            and Job Requirements section.
        
        '''
        
        self.VisitJobSites()
        self.ParseDescriptions()

    def OpenDBConnection(self):

        try:
            self.connection = sqlite3.connect("jobs.db")
            self.executor = self.connection.cursor()
            self.executor.execute("DROP TABLE IF EXISTS jobs")
            self.executor.execute("CREATE TABLE jobs (job text, percentage real, matched text)")
            self.connection.commit()
        except:
            print("DB connection refused ", sys.exc_info()[0])
        
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
        def VisitJobSitesWorker(string, SecondAttempt=False):
            
            try:
                self.Jobs.append(str(urlopen(string, timeout=5).read()))
            except:
                if SecondAttempt is False:
                    sleep(1.0)
                    VisitJobSitesWorker(string, SecondAttempt=True)
        
        Threads = []
        for job in self.JobLinks:
            Threads.append(Thread(target=VisitJobSitesWorker, args=("https://www.careerbuilder.com" + job,)))
        
        for thread in Threads:
            thread.start()
            sleep(0.025)
        for thread in Threads:
            thread.join()
            
    def ParseDescriptions(self):
        
        fp = None
        
        CanonicalLinks = []
        for i, Job in enumerate(self.Jobs):
            
            words_matched = ""
            HowManyKeyWordsFound = 0
            for Keyword in self.KeyWords:
                if Keyword in self.GetJobRequirements(Job):
                    HowManyKeyWordsFound += 1
                    words_matched += Keyword + " "
                    
            if HowManyKeyWordsFound == 0:
                #If no Keywords are found, then this job listing is not worth looking at.
                continue
            else:
                CanonicalLink = self.FindCanonicalLinkFromJobData(Job)
                #This conditional checks to make sure the link is unique.
                if self.VerifyUniqueCanonicalLink(CanonicalLinks, CanonicalLink) is True:
                    
                    CanonicalLinks.append(CanonicalLink)
                    KeyWordPercentage = (float(HowManyKeyWordsFound)/float(len(self.KeyWords)))*100.0
                    self.executor.execute("INSERT INTO jobs VALUES ('%s',%f, '%s')" % (CanonicalLink, KeyWordPercentage, words_matched))
                    PreviousCanonicalLink = CanonicalLink
        
        self.connection.commit()
            
    def VerifyUniqueCanonicalLink(self, CanonicalLinks, CanonicalLink):
        
        for link in CanonicalLinks:
            if CanonicalLink in link:
                #False if link is not unique
                return False
        
        #True if the link is unique
        return True
        
    def FindCanonicalLinkFromJobData(self, RawJobData):
        
        googlebotIndex = RawJobData.find("googlebot")
        CanonicalIndex = RawJobData.find("rel=\'canonical\'")
        tempJobData = RawJobData[googlebotIndex:CanonicalIndex]
        
        httpsindex = tempJobData.find("https")
        lastapos   = tempJobData.find("\'", httpsindex)
        
        return tempJobData[httpsindex:lastapos]
        
    def GetJobDescription(self, RawJobData):
        
        StartOfDescription = RawJobData.find("<h3>Job Description</h3>")
        EndOfDescription = RawJobData.find("</div>",StartOfDescription)
        
        return RawJobData[StartOfDescription:EndOfDescription]
        
    def GetJobRequirements(self, RawJobData):
        
        StartOfRequirements = RawJobData.find("<h3>Job Requirements</h3>")
        EndOfRequirements = RawJobData.find("</div>",StartOfRequirements)
                
        return RawJobData[StartOfRequirements:EndOfRequirements]
        

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
