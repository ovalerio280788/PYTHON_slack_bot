import logging
import os
from time import time

from slackbot import SlackBot

logging.basicConfig(level=logging.DEBUG)

# Initializes your app with your bot token and signing secret
slack_bot = SlackBot()


@slack_bot.app.event("app_home_opened")
def update_home_tab(client, event, logger):
    if event['tab'] == 'home':
        try:
            # views.publish is the method that your app uses to push a view to the Home tab
            client.views_publish(
                # the user that opened your app's app home
                user_id=event["user"],
                # the view object that appears in the app home
                view={
                    "type": "home",
                    "callback_id": "home_view",
                    # body of the view
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": slack_bot.help_text(user_id=event['user'])
                            }
                        }
                    ]
                }
            )
        except Exception as e:
            logger.error(f"Error publishing home tab: {e}")


@slack_bot.app.command(command="/qa_sos")
def qa_sos(command, ack, respond):
    logging.info(command)
    if 'text' not in command \
            or command['text'].lower().startswith('help') \
            or command['text'].lower().startswith('-h'):
        ack(slack_bot.help_text(command['user_id']))
    else:
        try:
            guild, message = [x.strip() for x in command['text'].split(slack_bot.message_splitter)]

            if guild == 'admin':
                if message.lower() == 'list qa members':
                    ack("Working on it, please wait... :hourglass_flowing_sand:")
                    qa_gorilla_channel_id = slack_bot.channel_id(slack_bot.qa_channel_name, private_channel=True)
                    if qa_gorilla_channel_id:
                        users_in_channel, count_users = slack_bot.get_users_in_channel(
                            channel_id=qa_gorilla_channel_id
                        )

                        slack_bot.app.client.chat_postMessage(
                            channel=command['user_id'],
                            blocks=[
                                {
                                    "type": "header",
                                    "text": {
                                        "type": "plain_text",
                                        "text": "List of users in the qa_gorilla channel"
                                    }
                                },
                                {
                                    "type": "section",
                                    "text": {
                                        "type": "mrkdwn",
                                        "text": "|\t_name\t|\tprofile_email\t|\tprofile_title_\t|"
                                    }
                                },
                                {
                                    "type": "divider",
                                }
                            ],
                            attachments=[
                                {
                                    "color": "#2eb886",
                                    "text": users_in_channel,
                                    "footer": f"List of users ({count_users})",
                                    "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png",
                                    "ts": time()
                                }
                            ]
                        )
                    else:
                        ack(f":wrong: Not able to get information from channel: _*{slack_bot.qa_channel_name}*_ :wrong:")
                else:
                    ack(f":wrong: '{message}' is not a valid admin action. :wrong:")
            elif guild in slack_bot.current_guilds:
                channel_id = slack_bot.channel_id(f'ask-qa-{guild}')
                # Add the user to the right channel
                resp_add_to_channel, success_add_to_channel = slack_bot.add_user_to_channel(channel_id, command['user_id'])
                # send a message to the channel
                if success_add_to_channel or resp_add_to_channel == 'already_in_channel':
                    resp_message_sent, success_message_sent = slack_bot.send_message_to_channel(
                        channel_id=channel_id,
                        text=f"{f'Welcome to the channel' if success_add_to_channel else 'Hello'} <@{command['user_id']}>, "
                             f"\n\nPlease elaborate more about your question and someone in this channel "
                             f"will do his or her best to help you: ```Question: {message}```"
                    )

                if success_add_to_channel and success_message_sent:
                    # send message/notification into the current place notifying that something happened
                    ack(f"Hi <@{command['user_id']}>, \n\nThanks for reaching out the QA Practice. "
                        f"Now you are part of <#{channel_id}>, you will get more custom help into this channel, "
                        f"so please add more context in there :thank_you: !")
                else:
                    if resp_add_to_channel == "not_in_channel":
                        ack(f":warn::warn: The *QAPracticeBot* is not in channel '<#{channel_id}>' :warn::warn:")
                    elif resp_add_to_channel == 'already_in_channel':
                        ack(f"Hi <@{command['user_id']}>, \n\n:warn::warn: Thanks for reaching out the QA Practice. "
                            f"You are currently part of <#{channel_id}>, so please go ahead and elaborate more "
                            f"about your question into the channel. :warn::warn:")
            else:
                ack(":wrong: You are trying to reach out to an unexisting or unavailable guild. :wrong:")
        except Exception as e:
            ack(":wrong: Something went wrong with the structure in your request, please take a look on how to use the bot. :wrong:")
            ack(slack_bot.help_text(command['user_id']))


# Start your app
if __name__ == "__main__":
    slack_bot.app.start(port=int(os.environ.get("PORT", 3000)))
