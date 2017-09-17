#!/usr/bin/python
#This bot is based on the tutorial by shantnu
#Check out his tutorial at: pythonforengineers.com/build-a-reddit-bot-part-1
#Check out John Huttlinger too for his flair bot: github.com/JBHUTT09
#Check out bboe for his handling of the ratelimit: github.com/bboe 

import praw
import pdb
import os
import re
import datetime
import time
import sys

flairs = {'JP News': 's', 'JP Discussion': 's', 'JP PSA': 's', 'JP Spoilers': 's', 'NA News': 't', 'NA PSA': 't',
	'NA Spoilers': 't', 'NA Discussion': 't', 'News': 'd', 'Tips & Tricks': 'i', 'Fluff': 'b', 'Comic': 'b', 'Guide': 'i', 
	'PSA': 'k', 'Rumor': 'c', 'WEEKLY RANT': 'j', 'Translated': 'f', 'Story Translation': 'i', 'Discussion': 'i',
	'Poll': 'i', 'Moderator': 'a', 'Maintenance': 'c', 'Stream': 'a', 'OC': 'b', 'Cosplay': 'b'}


bot_name = "Mashu_Kyrielite"

#handle ratelimit issues by bboe
def handle_ratelimit(func, *args, **kwargs):

	while True:
		try:
			func(*args, **kwargs)
			break
		except praw.errors.RateLimitExceeded as error:
			print("\tSleeping for %d seconds" + error.sleep_time)
			time.sleep(error.sleep_time)

#finds the number of seconds that have past since posting
def cal_time_diff(post_time):
	time_now = datetime.datetime.utcnow()
	tdelta = time_now - post_time

	return tdelta.total_seconds()

#returns the utc time at the moment of function call
def time_now():
	
	return datetime.datetime.utcnow()

#converted utc timestamp of post to utc datetime object
def timestamp_to_UTC(timestamp):
	
	return datetime.datetime.utcfromtimestamp(timestamp)

#checks for flair comments from post author
def check_flair_comments(submission, posts_replied_to, drop_time_limit):
        #time of the creation of the post
        post_time = timestamp_to_UTC(submission.created_utc)
        #the number of seconds since the creation of the post
        time_diff = cal_time_diff(post_time)

        #if the post goes unflaired for a certain amount of time, the bot just stops checking on the post for flairs
        if submission.link_flair_text is None or (submission.link_flair_text == "New Post" and time_diff >= drop_time_limit):
		remove_post(submission, posts_replied_to)
		return
        
	#if user flairs post, remove from posts_replied_to text file to reduce the amount of work
	if submission.link_flair_text != "New Post":
		remove_submission_id(posts_replied_to, submission.id)

	#checks for missing flair	
	if submission.link_flair_text == "New Post":
		check_flair_helper(submission, posts_replied_to);

#removes flaired post from posts_replied_to list in order reduce space of text file
def remove_submission_id(posts_replied_to, submission_id):

	if submission_id in posts_replied_to:
		posts_replied_to.remove(submission_id)

#removes post from subreddit due to being un-flaired for a period of time
def remove_post(submission, posts_replied_to):
	remove_submission_id(posts_replied_to, submission.id)
	submission.mod.remove()
		
#return true if the flair is valid, otherwise false					
def check_valid_flair(flair):
	
	if flair in flairs:
		return True
	
	return False

#checks if the user already commented a flair and flairs the post for them
def check_flair_helper(submission, posts_replied_to):
        #holds the bot comment
        bot_comment = None
        #holds reply message
        reply_message = "I've done as you've asked, Senpai. Please remember to flair next time, unless you're a mobile user. Please continue to request my assistance in the future if that is the case.\n\n[](#thankyou)  "

	#loops through the top level comments of the post
        submission.comments.replace_more(limit=0) #submission.comments.list() shows all the comments, no matter the depth
	for top_level_comment in submission.comments: 
                #saves the bot comment in case the OP replied to the bot with a flair
                if top_level_comment.author == bot_name:
                    bot_comment = top_level_comment
                
		#checks the comment to see if it has the same author as the post and if they have potential flair
		if top_level_comment.author == submission.author and re.search("\[.*\]", top_level_comment.body) is not None:
			flair_comment = top_level_comment.body
                        flair = flair_comment[flair_comment.find("[")+1:flair_comment.find("]")]
			
			#if the flair is valid, the post is flaired and comment with confirmation
			if(check_valid_flair(flair)):
				top_level_comment.reply(reply_message + flair)
				submission.mod.flair(text=flair, css_class=flairs[flair])
				remove_submission_id(posts_replied_to, submission.id)
			
				return True

        #Scans second level comment for OP reply to get flair
        if bot_comment is not None:
            submission.comments.replace_more(limit=0)
            for second_level_comment in bot_comment.replies:
                if second_level_comment.author == submission.author and re.search("\[.*\]", second_level_comment.body) is not None:
                    flair_comment = second_level_comment.body
                    flair = flair_comment[flair_comment.find("[")+1:flair_comment.find("]")]

                    if(check_valid_flair(flair)):
                        second_level_comment.reply(reply_message + flair)
                        submission.mod.flair(text=flair, css_class=flairs[flair])
                        remove_submission_id(posts_replied_to, submission.id)

                        return True

	return False

#checks to see if post is flaired and the age of the post; if the post is "old" enough and unflaired, the bot comments;		
def check_for_flair(submission, posts_replied_to, message, time_limit, drop_time_limit):		
	#time of the creation of the post
	post_time = timestamp_to_UTC(submission.created_utc)
	#the number of seconds since the creation of the post
	time_diff = cal_time_diff(post_time)


	#if the post goes unflaired for a certain amount of time, the bot just stops checking on the post for flairs
	if submission.link_flair_text is None or (submission.link_flair_text == "New Post" and time_diff >= drop_time_limit):
		remove_post(submission, posts_replied_to)
		return
	
	#if the post has not been visited and time and flair conditions are true, the bot comments and adds it to the visited list
	if submission.id not in posts_replied_to:
		if(time_diff >= time_limit and submission.link_flair_text == "New Post"):
			if check_flair_helper(submission, posts_replied_to) == False:
				submission.reply(message)
				posts_replied_to.append(submission.id)




#Main Function
def main():
	bot = 'bot1'
	subreddit_name = "grandorder"
	post_limit = 5 #number of posts to be checked at a time
	time_limit = 180 #time limit (in seconds) for unflaired post before bot comment
	drop_time_limit = 3900 #time limit (in seconds) for bot to stop checking a post for a flair
        message = "Senpai! It seems you've forgotten to properly flair your post, but this kouhai will gladly do it for you. Simply reply to my comment with one of these [flairs](https://i.imgur.com/HiofxBg.png) and I'll change it myself. Just put the flair title inside brackets, like so '[Fluff]'." #Bot message

	#Do not change below here unless you know your stuff
	reddit = praw.Reddit(bot)
	subreddit = reddit.subreddit(subreddit_name)

	#creates/opens a text file that stores visited posts, so the bot does not span the post
	if not os.path.isfile("posts_replied_to.txt"):
		#if file does not exist, create a new list
		posts_replied_to = []
		temp_posts_replied_to = []

	else:
		#opens exisitng file and creates a list of content
		with open("posts_replied_to.txt", "r") as f:
			posts_replied_to = f.read()
			posts_replied_to = posts_replied_to.split("\n")
			posts_replied_to = list(filter(None, posts_replied_to))
			temp_posts_replied_to = list(filter(None, posts_replied_to))

	#try-catch for connection errors with reddit
	try:
		#loops through the post_limit number of new posts
		for submission in subreddit.new(limit=post_limit):
			#skip AutoModerator posts
			if submission.author == "AutoModerator":
				continue
		
			handle_ratelimit(check_for_flair, submission, temp_posts_replied_to, message, time_limit, drop_time_limit)
		
		#loops through the visited, unflaired posts for flair comments
		for post_id in posts_replied_to:
			missing_flair_post = reddit.submission(post_id)
			handle_ratelimit(check_flair_comments, missing_flair_post, temp_posts_replied_to, drop_time_limit)

	except Exception:
		sys.exc_clear()
	
	#writes the list back to the file	
	with open("posts_replied_to.txt", "w") as f:
		for post_id in temp_posts_replied_to:
			f.write(post_id + "\n")

main()	
