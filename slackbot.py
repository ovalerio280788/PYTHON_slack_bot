import os
import ssl

import jmespath
from bgcolors import BColors
from slack_bolt import App
from slack_sdk import WebClient


class SlackBot:
    def __init__(self):
        ssl._create_default_https_context = ssl._create_unverified_context
        if not os.environ.get("SLACK_BOT_TOKEN") and not os.environ.get("SLACK_SIGNING_SECRET"):
            print(f"""
            {BColors.FAIL}
            \rYOU NEED TO DEFINE THE FOLLOWING ENVIRONMENT VARIABLES TO BE ABLE TO CONTINUE: 
            \r\t- SLACK_BOT_TOKEN
            \r\t- SLACK_SIGNING_SECRET
            {BColors.ENDC}
            """)
            exit(1)

        self.app = App(
            token=os.environ.get("SLACK_BOT_TOKEN"),
            signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
        )
        self.slack_client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])
        self.qa_channel_name = 'qa_gorilla'
        self.message_splitter = '**'
        self.current_guilds = ['js', 'python']

    def help_text(self, user_id):
        '''
        This method returns a formated string with a help about how to use this slack bot.
        :param user_id: The user id, used to provide a warm welcome in the help text.
        :return: A string with the complete help guide
        '''
        return f":Wave: *Welcome {self.user_email(user_id=user_id)} to QAPracticeBot*" \
               f"\n\nQAPracticeBot allows you to ask questions and then you get support from other QA members." \
               f"\n\n\n\n*Documentation:* :books:" \
               f"\n\nYou can perform the following SOS actions:" \
               f"\n\t\t- `help`" \
               f"\n\t\t- `-h`" \
               f"\n\t\t- `/qa_sos qa_fundamentals {self.message_splitter} Brief summary of your question`" \
               f"\n\t\t- `/qa_sos js {self.message_splitter} Brief summary of your question`" \
               f"\n\t\t- `/qa_sos java {self.message_splitter} Brief summary of your question`" \
               f"\n\t\t- `/qa_sos python {self.message_splitter} Brief summary of your question`" \
               f"\n\nYou can perform the following administrative actions:" \
               f"\n\t\t- `/qa_sos admin {self.message_splitter} List QA members`" \
               f"\n\n\n\n\n\n_PLEASE CONTACT THE QA PRACTICE LEADS FOR ANY FEEDBACK._ :thank_you:"

    def user_info(self, user_id):
        '''
        This method get all the user information from slack as an object
        :param user_id: the id of the user to find its information
        :return: All the information of the user in a single object
        '''
        return self.slack_client.users_info(user=user_id).data

    def user_email(self, user_id):
        '''
        This method get the user email from slack
        :param user_id: the id of the user to find its email
        :return: The user email
        '''
        return jmespath.search('user.profile.email', self.user_info(user_id=user_id))

    def channel_info(self, channel_name, private_channel=False):
        '''
        This method finds a channel into the list of slack channels
        :param channel_name: The channel name to find into the bunch of channels
        :private_channel: If you want to fin the channel as private of public channel. False by default.
        :return: A channel object with all the information about the channel
        '''
        channels = jmespath.search(
            f'[?name==`{channel_name}`]',
            self.slack_client.conversations_list(
                limit=1000,
                types=f"private_channel" if private_channel else "public_channel",
                exclude_archived=True
            ).data['channels']
        )
        return channels[0] if channels else None

    def channel_id(self, channel_name, private_channel=False):
        '''
        This method gets the channel id based on a given channel name
        :param channel_name: The channel name to get its id
        :private_channel: If you want to fin the channel as private of public channel. False by default.
        :return: A channel id
        '''
        channel = self.channel_info(channel_name, private_channel)
        return jmespath.search('id', channel)

    def add_user_to_channel(self, channel_id, users):
        '''
        This method adds a given user to a given channel
        :param channel_id: The Channel id to add the user
        :param users: The users to be added to the channel
        :return: A tuple of 2 values
                    - The first value is the response object of the slack client request (conversations_invite)
                    - The second value is a boolean value that represents if the request was success or not
        '''
        try:
            return self.slack_client.conversations_invite(channel=channel_id, users=users), True
        except Exception as e:
            return e.response.data['error'], False

    def send_message_to_channel(self, channel_id, text):
        '''
        This method is in charged of sending a given message to a given channel
        :param channel_id: The channel that will receive the message
        :param text: The message to send to the channel
        :return: A tuple of 2 values
                    - The first value is the response object of the slack client request (chat_postMessage)
                    - The second value is a boolean value that represents if the request was success or not
        '''
        try:
            return self.slack_client.chat_postMessage(
                channel=channel_id,
                text=text
            ), True
        except Exception as e:
            return e.response.data['error'], False

    def get_users_in_channel(self, channel_id):
        '''
        This method gets all users/members that belong to a given channel id
        :param channel_id: The channel id to get users/members
        :return: A tuple of 2 values:
            - a list of users separated by comma.
            - number of users/members exluding bot user types.
        '''
        members = self.slack_client.conversations_members(channel=channel_id, limit=1000).data['members']
        users_as_text = ''
        count = 0
        for member in members:
            info = self.user_info(member)
            if not info['user']['is_bot']:
                users_as_text += f"{info['user']['name']}," \
                                 f"{info['user']['profile']['email']}," \
                                 f"{info['user']['profile']['title']}\n"
                count+=1
        return users_as_text, count
