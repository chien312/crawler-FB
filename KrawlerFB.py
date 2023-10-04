"""
This is the main script of the KrawlerFB.
-----------------------------------------------------------------

KrawlerFB is a simple crawler for Facebook.
Users can specify the group and the number of posts they
want to crawl within KrawlerFB. Before using this crawler to 
obtain any post in the group, loging in is required. 
Please make sure you enter the right email and password, also
only the group your account joining in can be crawled.

This program is mainly checking for the command user inputed, if
the command is valid, it will do the crawling and print out the 
success message.
"""
import crawler 
import getopt, sys # to deal with command line arguments
from getpass import getpass # make password invisible

dataSet = [
    # we have 8 columns in each row
    # ["POST_ID", "AUTHOR", "CONTENT", "TIME_STAMP", "COMMENTS", "COMMENTERS", "POLARITY", "IMG_SRC"]
]

def main():
    # Set the default values
    group = 'pythontw'
    totalPost = 10

    # Read the command line arguments
    argv = sys.argv[1:]

    try:
        # Command line argument:
        # -g: the group user want to crawl
        # -n: the number of posts user want to crawl
        opts, args = getopt.getopt(argv, "g:n:")

    except:
        # If user input an invalid command line argument, print error message
        print("[Error] invalid argument")

    # Parse the argument
    for opt,arg in opts:
        # Read the -g argument
        if opt in ['-g']:
            group = arg
        # Read the -n argument
        elif opt in ['-n']:
            totalPost = int(arg) # cast the input to int type
            # Check if the number of posts user input is positive
            # If not, print the error message and return
            if(totalPost <= 0):
                print('[ERROR] number of posts should be positive.')
                return 1
    
    # Log in Facebook
    email = input("Please enter your email:\n")
    password = getpass("Please enter your password:\n")

    # Check if the group user input exists
    # The function crawl() will execute the crawling work.
    valid = crawler.crawl(email, password, group, totalPost, dataSet)
    if(valid == 0):
        # If the group user input exists, crawl() will crawl the user-specific number of posts in the specific board
        # and return 0, printing out the success message
        print('KrawlerFB executed successfully. The result was output as "output.csv".')
    elif(valid == -1):
        # If the given account cannot be loged in, it returns -1
        print('Wrong email or password, please try again.')
    elif(valid == -2):
        # If the group doesn't exist, it returns -2
        print('[ERROR] The Facebook group does not exist.')

    # End the program if successfully executed
    return 0

if __name__ == '__main__':
    main()
