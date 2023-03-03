from time import gmtime, strftime

import requests
import json
import random

from server import database


class Webhooks:
    """
    Contains functions related to webhooks.
    """

    def __init__(self, server):
        self.server = server

    def send_webhook(
        self,
        username=None,
        avatar_url=None,
        message=None,
        embed=False,
        title=None,
        description=None,
        url=None,
    ):
        is_enabled = self.server.config["webhooks_enabled"]
        if url is None:
            url = self.server.config["webhook_url"]

        if not is_enabled:
            return

        data = {}
        data["content"] = message
        data["avatar_url"] = avatar_url
        data["username"] = username if username is not None else "tsuserver webhook"
        if embed is True:
            data["embeds"] = []
            embed = {}
            embed["description"] = description
            embed["title"] = title
            data["embeds"].append(embed)
        result = requests.post(
            url, data=json.dumps(data), headers={"Content-Type": "application/json"}
        )
        try:
            result.raise_for_status()
        except requests.exceptions.HTTPError as err:
            database.log_misc("webhook.err", data=err.response.status_code)
        else:
            database.log_misc(
                "webhook.ok",
                data="successfully delivered payload, code {}".format(
                    result.status_code
                ),
            )

    def modcall(self, char, ipid, area, reason=None):
        is_enabled = self.server.config["modcall_webhook"]["enabled"]
        username = self.server.config["modcall_webhook"]["username"]
        avatar_url = self.server.config["modcall_webhook"]["avatar_url"]
        no_mods_ping = self.server.config["modcall_webhook"]["ping_on_no_mods"]
        mod_role_id = self.server.config["modcall_webhook"]["mod_role_id"]
        mods = len(self.server.client_manager.get_mods())
        current_time = strftime("%H:%M", gmtime())

        if not is_enabled:
            return

        if mods == 0 and no_mods_ping:
            message = f"@{mod_role_id if mod_role_id is not None else 'here'} A user called for a moderator, but there are none online!"
        else:
            if mods == 1:
                s = ""
            else:
                s = "s"
            message = f"New modcall received ({mods} moderator{s} online)"

        description = f"[{current_time} UTC] {char} ({ipid}) in [{area.id}] {area.name} {'without reason (using <2.6?)' if reason is None else f'with reason: {reason}'}"

        self.send_webhook(
            username=username,
            avatar_url=avatar_url,
            message=message,
            embed=True,
            title="Modcall",
            description=description,
        )
    
    def advert(self, char, area, msg=None):
        is_enabled = self.server.config["advert_webhook"]["enabled"]
        username = self.server.config["advert_webhook"]["username"]
        avatar_url = self.server.config["advert_webhook"]["avatar_url"]

        if not is_enabled:
            return
        
        title_list = self.server.misc_data['advert_titles']

        # Role pings hardcoded uh oh
        roles = {}
        for key in ["def", "defense"]:
            roles[key] = "<@&1080312713181409400>"
        for key in ["pro", "prosecution"]:
            roles[key] = "<@&1080312912603779122>"
        for key in ["wit", "witness", "det", "detective"]:
            roles[key] = "<@&1080455427587842078>"
        for key in ["jud", "judge"]:
            roles[key] = "<@&1080455480985522226>"
        for key in ["steno", "stenographer"]:
            roles[key] = "<@&1080455505455087676>"

        pings = []
        check = msg.lower()
        if "all" in check:
            for x in roles:
                if x in roles and roles[x] not in pings:
                    pings.append(roles[x])
        else:
            for x in check.split():
                if x in roles and roles[x] not in pings:
                    pings.append(roles[x])

        message = f"{random.choice(title_list)}\n"
        message += " ".join(pings)

        description = f"{char} in {area.name} {'needs people for a case!' if msg is None else f'needs {msg}'}"

        self.send_webhook(
            username=username,
            avatar_url=avatar_url,
            message=message,
            embed=True,
            title="❗ Case Advert ❗",
            description=description,
            url=self.server.config["advert_url"]
        )

    def kick(self, ipid, hdid, reason="", client=None, char=None):
        is_enabled = self.server.config["kick_webhook"]["enabled"]
        username = self.server.config["kick_webhook"]["username"]
        avatar_url = self.server.config["kick_webhook"]["avatar_url"]

        if not is_enabled:
            return

        message = f"{char} (IPID: {ipid}, HDID: {hdid})" if char is not None else str(ipid)
        message += " was kicked"
        message += (
            f" by {client.name} ({client.ipid})"
            if client is not None
            else " from the server"
        )
        message += (
            f" with reason: {reason}"
            if reason.strip() != ""
            else " (no reason provided)."
        )

        self.send_webhook(username=username,
                          avatar_url=avatar_url, message=message)

    def ban(
        self,
        ipid,
        ban_id,
        reason="",
        client=None,
        hdid=None,
        char=None,
        unban_date=None,
    ):
        is_enabled = self.server.config["ban_webhook"]["enabled"]
        username = self.server.config["ban_webhook"]["username"]
        avatar_url = self.server.config["ban_webhook"]["avatar_url"]
        unban_date = strftime("%Y-%m-%d %H:%M:%S %Z")

        if not is_enabled:
            return
        message = f"{char} (IPID: {ipid}, HDID: {hdid})" if char is not None else str(ipid)
        message += (
            f" was hardware-banned"
            if hdid is not None
            else " was banned"
        )
        message += (
            f" by {client.name} ({client.ipid})"
            if client is not None
            else " from the server"
        )
        message += f" with reason: {reason}" if reason.strip() != "" else ""
        message += f" (Ban ID: {ban_id}).\n"
        message += (
            f"It will expire {unban_date}"
            if unban_date is not None
            else "It is a permanent ban."
        )

        self.send_webhook(username=username,
                          avatar_url=avatar_url, message=message)

    def unban(self, ban_id, client=None):
        is_enabled = self.server.config["unban_webhook"]["enabled"]
        username = self.server.config["unban_webhook"]["username"]
        avatar_url = self.server.config["unban_webhook"]["avatar_url"]

        if not is_enabled:
            return

        message = f"Ban ID {ban_id} was revoked"
        message += (
            f" by {client.name} ({client.ipid})."
            if client is not None
            else " by the server."
        )

        self.send_webhook(username=username,
                          avatar_url=avatar_url, message=message)
        
    
    def warn(self, ipid, hdid, reason="", client=None, char=None):
        is_enabled = self.server.config["warn_webhook"]["enabled"]
        username = self.server.config["warn_webhook"]["username"]
        avatar_url = self.server.config["warn_webhook"]["avatar_url"]

        if not is_enabled:
            return

        message = f"{char} (IPID: {ipid}, HDID: {hdid})" if char is not None else str(ipid)
        message += " was warned"
        message += (
            f" by {client.name} ({client.ipid})"
            if client is not None
            else " from the server"
        )
        message += (
            f" with reason: {reason}"
            if reason.strip() != ""
            else " (no reason provided)."
        )

        self.send_webhook(username=username,
                          avatar_url=avatar_url, message=message)
