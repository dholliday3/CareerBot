"""
Simple Facebook Echo bot: Respond with exactly what it receives
Standalone version
"""

import sys, json, traceback, requests, apiai
from flask import Flask, request
from pymongo import MongoClient
from pprint import pprint
import flask

application = Flask(__name__)
app = application


#facebook
PAT = 'EAADy0n6REeMBAOZB0JWWXvJZCMT2SZAqYZBYWrhWWJia4Tj9ZBpjf3ZB6besz6tS71wZBcrZBsk7KVzls0BCa86JZBkMY7l4JnHiNXYFmfKHnuKh2kruEl2dqaBrnk04fsXQdJrdubisPVXvQbU3abbvrSRzdgEsGLlpwjHJDAzbQZBzET7Bv6QW76'
VERIFICATION_TOKEN = 'replace_your_own_token'

# ======================= connecting to page ===========================
@app.route('/', methods=['GET'])
def handle_verification():
    print "Handling Verification."
    if request.args.get('hub.verify_token', '') == VERIFICATION_TOKEN:
        print "Webhook verified!"
        return request.args.get('hub.challenge', '')
    else:
        return "Wrong verification token!"

# ======================= Global Varibales ===========================
#MongoDB
MONGO_CONNECTION ='mongodb://GTCareerBot:CareerFair2017!@jobbot-shard-00-00-kjbwt.mongodb.net:27017,jobbot-shard-00-01-kjbwt.mongodb.net:27017,jobbot-shard-00-02-kjbwt.mongodb.net:27017/test?ssl=true&replicaSet=JobBot-shard-0&authSource=admin'
mongo_client = MongoClient(MONGO_CONNECTION)
profile_posts = mongo_client.careerbot_database.profiles #profile db
company_posts = mongo_client.careerbot_database.companies #company db
#apiai
APIAI_CLIENT_ACCESS_CODE = "bf223d0a505f4e2294e4e04ee1991ce8"
try:
    ai = apiai.ApiAI(APIAI_CLIENT_ACCESS_CODE)
except:
    print "connection didn't work"

#Synonym lists --> used for determining similar words
MAJOR_DICT = {
    #"cm": ["CM", "COMPUTATIONALMEDIA", "COMPUTATIONAL MEDIA"],
    "Computer Science": ["CS", "COMPSCI", "COMP SCI", "COMPUTER SCIENCE"],
    #"compE": ["COMP E", "COMPE", "COMPUTER ENGINEERING"],
    #"doubleE": ["DOUBLE E", "EE", "ELECTRICAL ENGINEERING"],
    "Industrial Engineering": ["IE", "ISYE", "INDUSTRIAL ENGINEERING", "ISE"],
    "Mechanical Engineering": ["ME", "MECHANICAL", "MECHANICAL ENGINEERING"]
}

POSITION_DICT = {
    "Co-op": ["COOP", "CO OP", "FALL COOP", "CO-OP", "CO-OP"],
    "Internship": ["INTERNSHIP", "INTERN", "INTERNSHIP"],
    "Full-time": ["FULLTIME", "FULL TIME", "FULL-TIME", "FT"],
    "Part-time": ["PART-TIME", "PART TIME", "PARTTIME", "PT"]
}

# ======================= Bot processing ===========================
@app.route('/', methods=['POST'])
def handle_messages():
    payload = request.get_data()

    # Handle messages
    for sender_id, message in messaging_events(payload):
        # Start processing valid requests
        print 'handle_message sender_id: ' + sender_id + '\n'
        try:
            response = processIncoming(sender_id, message)

            if response is not None:
                send_message(PAT, sender_id, response)

            else:
                send_message(PAT, sender_id, "Sorry I don't understand that")
        except Exception, e:
            print e
            traceback.print_exc()
    return "ok"

#determine what type of message
def processIncoming(user_id, message):
    print "User ID BOI: " + str(user_id)
    if message['type'] == 'text':
        message_text = message['data']
        print "we in text"
        return message_text

    elif message['type'] == 'location':
        response = "I've received location (%s,%s) (y)"%(message['data'][0],message['data'][1])
        return response

    elif message['type'] == 'audio':
        audio_url = message['data']
        return "I've received audio %s"%(audio_url)

    # Unrecognizable incoming, remove context and reset all data to start afresh
    else:
        return "*scratch my head*"


######
# Message Flow determined each time hit send_message()
######

#send message back

def send_message(token, user_id, text):
    """Send the message text to recipient with id recipient.
    """

    #        1   USERID_ONLY
    #        2   USERID_NAME_ONLY
    #        3   USERID_NAME_MAJOR_ONLY
    #        4   USERID_NAME_MAJOR_YEAR_ONLY
    #        5   ALL
    #        6   None <- type<Nonetype>

    ### CASE 1 - if user id not in databasee
    # --> greet and make profile
    # Case 1.1 - if user ID in database but major == "", year == "", position == "", name==""
    # Case 1.2 - if user ID, major, in db --> rest not
    # Case 1.3 - etc.

    ### CASE 2 - if user id + the rest are in db --> connect to apiai

    # CASE 1
    if user_id == "1357746954334750":
        #r = send_message_helper(token, user_id, text)
        print 'case where user_id from sender'
    else:
        print 'case where user'
        if checkProfile(user_id) == None:
            print "NOT IN DB"
            #put userID in db
            make_stu_profile(user_id, "", "", "", "")
            r = send_message_helper(token, user_id, "Hi, look at me! I'm your friendly Career Fair Mr. Meeseeks! \nLet's start by building your profile. \nWhat extra saucy name should I call you?")
            '''
            r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                  params={"access_token": token},
                  data=json.dumps({
                      "recipient": {"id": user_id},
                      "message": {message_to_user.decode('unicode_escape')}
                  }),
                  headers={'Content-type': 'application/json'})
            '''
        #Case 1.1
        elif checkProfile(user_id) == 'USERID_ONLY':
            print "IN DB"
            #put name from text in db
            make_stu_profile(user_id, text, "", "", "")
            r = send_message_helper(token, user_id, "What is your major (if you have 2 put the one you want to find a job with)?")
            #call put
        #Case 1.2
        elif checkProfile(user_id) == 'USERID_NAME_ONLY':
            print "USERID_NAME_ONLY"
            #put major in db
            make_stu_profile(user_id, "", text, "", "")
            r = send_message_helper(token, user_id, "What year are you? It's ok you 5th year - I'm a 7th year and a freshman by credit hrs :) ?")
        #Case 1.3
        elif checkProfile(user_id) == 'USERID_NAME_MAJOR_ONLY':
            print 'USERID_NAME_MAJOR_ONLY'
            #put major in db
            make_stu_profile(user_id, "", "", text, "")
            r = send_message_helper(token, user_id, "What kind of jobs are you looking for (i.e. internship, co-op, full-time)?")
        #Case 1.4
        elif checkProfile(user_id) == 'USERID_NAME_MAJOR_YEAR_ONLY':
            print 'USERID_NAME_MAJOR_YEAR_ONLY'
            #put positions in db
            make_stu_profile(user_id, "", "", "", text)
            user_json = profile_posts.find_one({'user_id': user_id})
            company_list = findCompanies(user_json['major'], user_json['positions'])

            r = send_message_helper(token, user_id, "Awesome, here are the companies you should talk to: \n" + company_list[0] + "\n" + company_list[1] + "\n" + company_list[2])
        #Case 1.5
        #Case 2
        elif checkProfile(user_id) == 'ALL':
            print 'ALL'
            #r = send_message_helper(token, user_id, "Welcome back! Ask me any question!")

            #use apiai to determine intent
            users_intent, intent_response = getIntent(text)
            if users_intent != None:
                print "users_inent" + users_intent

                if users_intent == "general_info":
                    company = intent_response['result']['parameters']['Company']
                    company_info = getCompanyInfo(company)
                    r = send_message_helper(token, user_id, company_info)
                elif users_intent == "tech_stack":
                    company = intent_response['result']['parameters']['Company']
                    company_info = getCompanyTechStack(company)
                    r = send_message_helper(token, user_id, company_info)
                elif users_intent == "url":
                    company = intent_response['result']['parameters']['Company']
                    company_info = getCompanyURL(company)
                    r = send_message_helper(token, user_id, company_info)
                elif users_intent == 'location':
                    print ''
                    company = intent_response['result']['parameters']['Company']
                    company_info = getCompanyLocation(company)
                    r = send_message_helper(token, user_id, company_info)
            else:
                print "didn't get it"
        #Case 2
        else:
            print 'Case 2'

        '''
        r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                          params={"access_token": token},
                          data=json.dumps({
                              "recipient": {"id": user_id},
                              "message": {"text": text.decode('unicode_escape')}
                          }),
                          headers={'Content-type': 'application/json'})

        '''
    #if r.status_code != requests.codes.ok:
    #    print r.text

#helper method for send messages

def send_message_helper(token, user_id, message_to_user):
    print "message type: " + str(type(message_to_user))
    message_to_user = str(message_to_user)

    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
              params={"access_token": token},
              data=json.dumps({
                  "recipient": {"id": user_id},
                  "message": {"text": message_to_user.decode('unicode_escape')} #"message": {message_to_user.decode('unicode_escape')}
              }),
              headers={'Content-type': 'application/json'})
    '''
    facebook_data = flask.jsonify({"recipient": {"id": user_id},
                  "message": {message_to_user.decode('unicode_escape')}})
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
              params={"access_token": token},
              data= facebook_data,
              headers={'Content-type': 'application/json'})
    '''
    return r


# Generate tuples of (sender_id, message_text) from the provided payload.
# This part technically clean up received data to pass only meaningful data to processIncoming() function
def messaging_events(payload):

    data = json.loads(payload)
    messaging_events = data["entry"][0]["messaging"]

    for event in messaging_events:
        sender_id = event["sender"]["id"]

        # Not a message
        if "message" not in event:
            yield sender_id, None

        # Pure text message
        if "message" in event and "text" in event["message"] and "quick_reply" not in event["message"]:
            data = event["message"]["text"].encode('unicode_escape')
            yield sender_id, {'type':'text', 'data': data, 'message_id': event['message']['mid']}


        # Message with attachment (location, audio, photo, file, etc)
        elif "attachments" in event["message"]:

            # Location
            if "location" == event['message']['attachments'][0]["type"]:
                coordinates = event['message']['attachments'][
                    0]['payload']['coordinates']
                latitude = coordinates['lat']
                longitude = coordinates['long']

                yield sender_id, {'type':'location','data':[latitude, longitude],'message_id': event['message']['mid']}

            # Audio
            elif "audio" == event['message']['attachments'][0]["type"]:
                audio_url = event['message'][
                    'attachments'][0]['payload']['url']
                yield sender_id, {'type':'audio','data': audio_url, 'message_id': event['message']['mid']}

            else:
                yield sender_id, {'type':'text','data':"I don't understand this", 'message_id': event['message']['mid']}


        # Quick reply message type
        elif "quick_reply" in event["message"]:
            data = event["message"]["quick_reply"]["payload"]
            yield sender_id, {'type':'quick_reply','data': data, 'message_id': event['message']['mid']}
        else:
            yield sender_id, {'type':'text','data':"I don't understand this", 'message_id': event['message']['mid']}

# ======================= APIAI Stuff ===========================
#get users intent using apiai
def getIntent(user_input):
    #send use text
    request = ai.text_request()
    request.query = str(user_input)

    #receiving responce
    response = json.loads(request.getresponse().read().decode('utf-8'))
    responseStatus = response['status']['code']
    if (responseStatus == 200):
        # Sending the textual response of the bot.
        pprint(response)
        try:
            users_intent = response['result']['metadata']['intentName']
        except:
            users_intent = None
        return users_intent, response
    else:
        return "ERROR WITH APIAI!!!"

#####
# intent methods
#####

#query database with company
def get_company_from_db(company):
    company_response = company_posts.find_one({'company_name': company})
    if company_response != None:
        return company_response
    else:
        return None

def getCompanyInfo(company):
    company_response = get_company_from_db(company)
    if company_response != None:
        return company_response['general_info']
    else:
        return 'Company not found'

def getCompanyTechStack(company):
    company_response = get_company_from_db(company)
    if company_response != None:
        tech_stack = ""
        for i in company_response['tech_stack']:
            tech_stack += i + "\n"
        return tech_stack
    else:
        return 'Company not found'
def getCompanyURL(company):
    company_response = get_company_from_db(company)
    if company_response != None:
        return company_response['url']
    else:
        return 'Company not found'

def getCompanyLocation(company):
    company_response = get_company_from_db(company)
    if company_response != None:
        return company_response['location'][0]
    else:
        return "Company not found"

# ======================= normalize major ===========================
def majors(input_major):
    input_major = str(input_major).upper().strip()
    maj = None
    for key in MAJOR_DICT.keys():
        for listElement in MAJOR_DICT[key]:
            if input_major == listElement:
                maj = key
    return maj

def positions(input_pos):
    input_pos = input_pos.upper().strip()
    pos = None
    for key in POSITION_DICT.keys():
        for listElement in POSITION_DICT[key]:
            if input_pos == listElement:
                pos = key
    return pos

def emailShorten(email):
    newStr = ""
    push = True
    count = 0
    while push:
        if email[count] != "@":
            newStr += email[count]
            count += 1
        else:
            push = False
    return newStr

# ======================= Making Profile ===========================
#returns what has in profile
# @returns string
#        1   USERID_ONLY
#        2   USERID_NAME_ONLY
#        3   USERID_NAME_MAJOR_ONLY
#        4   USERID_NAME_MAJOR_YEAR_ONLY
#        5   ALL
#        6   None <- type<Nonetype>
def checkProfile(user_id):
    print "\n checking profile - UserID = " + str(user_id)
    user_id = str(user_id)
    student = profile_posts.find_one({'user_id': user_id})
    if student == None:
        return None
    else:
        #1
        user_json = profile_posts.find_one({'user_id': user_id})
        #pprint(user_json)

        if user_json['name'] == "" and user_json['major'] == '' and user_json['year'] == '' and user_json['positions'] == '':
            return "USERID_ONLY"
        #2
        elif user_json['name'] != "" and user_json['major'] == '' and user_json['year'] == '' and user_json['positions'] == '':
            return 'USERID_NAME_ONLY'
        #3
        elif user_json['name'] != "" and user_json['major'] != '' and user_json['year'] == '' and user_json['positions'] == '':
            return 'USERID_NAME_MAJOR_ONLY'
        #4
        elif user_json['name'] != "" and user_json['major'] != '' and user_json['year'] != '' and user_json['positions'] == '':
            return 'USERID_NAME_MAJOR_YEAR_ONLY'
        elif user_json['name'] != "" and user_json['major'] != '' and user_json['year'] != '' and user_json['positions'] != '':
            return 'ALL'
        else:
            print "there was an error when creating a new person"
            return None

def make_stu_profile(user_id, user_name, user_major, user_year, user_position):
    print "\n MAKING STUDENT PROFILE \n"
    #print "user_id: " + user_id
    if user_id != "" and user_name == "" and user_major == "" and user_position == "" and user_year == "":
        data = {
            'user_id': user_id,
            'name': '',
            'major': '',
            'positions': '',
            'year': ''
        }
        profile_posts.insert(data, data, )
        print 'updated database with: ' + str(user_id)

    elif user_id != "" and user_name != "" and user_major == "" and user_position == "" and user_year == "":
        print "adding user_name"
        profile_posts.update({"user_id": user_id}, {"$set": {"name": user_name}}, upsert=False)

    elif user_id != "" and user_name == "" and user_major != "" and user_position == "" and user_year == "":
        print "adding user_major"
        user_major = majors(user_major)
        profile_posts.update({"user_id": user_id}, {"$set": {"major": user_major}}, upsert=False)

    elif user_id != "" and user_name == "" and user_major == "" and user_year != "" and user_position == "":
        print "adding user_year"
        profile_posts.update({"user_id": user_id}, {"$set": {"year": user_year}}, upsert=False)

    elif user_id != "" and user_name == "" and user_major == "" and user_year == "" and user_position != "":
        print "adding user_position"
        user_position = positions(user_position)
        profile_posts.update({"user_id": user_id}, {"$set": {"positions": user_position}}, upsert=False)

    else:
        print "wasnt' able to update"

    '''
    else:
        print "Welcome back!"
        major = student['major']
        year = student['year']
        position = student['positions']
    '''
    #findCompanies(major, position) #--> need to call this tho

# ======================= List of Companies ===========================
def matchCompaniesByMajor(major):
    matched_list1 = []
    for company in company_posts.find({'majors': major}):
        matched_list1 += [company['company_name']]
    # print(matched_list1)
    return matched_list1

def matchCompaniesByPositions(position):
    matched_list2 = []
    for company in company_posts.find({'positions': position}):
        matched_list2 += [company['company_name']]
    # print(matched_list2)
    return matched_list2

def findCompanies(major, position):
    matched_list1 = matchCompaniesByMajor(major)
    matched_list2 = matchCompaniesByPositions(position)

    final_matched_list = []
    for company in matched_list1:
        if company in matched_list2:
            final_matched_list += [company]

    print "These companies are looking for you!"
    count = 1
    for c in final_matched_list:
        print str(count) + ": " + c
        count += 1

    return final_matched_list



# ======================= Run App ===========================
# Allows running with simple `python <filename> <port>`
if __name__ == '__main__':
    if len(sys.argv) == 2: # Allow running on customized ports
        app.run(port=int(sys.argv[1]))
    else:
        app.run() # Default port 5000
