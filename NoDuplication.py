
import sqlite3

connection = None
cursor = None

def main():
    
    InitializeDatabase()
    StartNonDuplicationAlgorithm()
    CloseDatabase()

def StartNonDuplicationAlgorithm():

    global cursor
    global connection

    oldarray = GetArrayOfOldTable()

    for i in range(len(oldarray)):
        foundSame = False
        for j in range(i+1, len(oldarray)):
            if oldarray[i][0] in oldarray[j][0]:
                foundSame = True
                break
        if not foundSame:
            cursor.execute("INSERT INTO noduplicates VALUES ('%s',%f)" % (oldarray[i][0],oldarray[i][1]))

    connection.commit()


def GetArrayOfOldTable():

    global cursor

    cursor.execute("SELECT * FROM jobs")
    return cursor.fetchall()

def InitializeDatabase():

    global connection
    global cursor

    connection = sqlite3.connect("jobs.db")
    cursor = connection.cursor()

    DropTableIfExists(connection, cursor)
    CreateTable(connection, cursor)

def CloseDatabase():
    
    global connection
    connection.close()

    

def CreateTable(connection, cursor):

    cursor.execute("CREATE TABLE noduplicates (job text, percentage real)")
    connection.commit()

def DropTableIfExists(connection, cursor):

    try:
        cursor.execute("DROP TABLE noduplicates")
        connection.commit()
    except:
        pass

if __name__ == '__main__':
    import sys
    sys.exit(main())