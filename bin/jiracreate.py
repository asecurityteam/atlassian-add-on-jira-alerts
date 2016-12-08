#!/usr/bin/env python

import sys

from splunklib.searchcommands import \
    dispatch, ReportingCommand, Configuration, Option, validators

from common import fetch_jira, submit_issue
from jira_issue import NewIssue

import logging
logger = logging.getLogger('JiraCreateCommand')


@Configuration()
class JiraCreateCommand(ReportingCommand):
    """
    """

    # determine if we want to actually send this metric to dd
    send = Option(require=False, default=False, validate=validators.Boolean())
    jira = Option(name="jira", require=False, default='default')
    description = Option(require=False, default=None)
    title = Option(require=False, default=None)
    project = Option(require=False, default=None)
    issue_type = Option(require=False, default=None)
    send = Option(require=False, default=False, validate=validators.Boolean())

    def get_owner(self):
        owner = getattr(self, "owner", None)
        return owner or self._metadata.searchinfo.owner

    def get_sid(self):
        sid = getattr(self, "sid", None)
        return sid or self._metadata.searchinfo.sid

    def get_session_key(self):
        key = getattr(self, "session_key", None)
        return key or self._metadata.searchinfo.session_key

    def get_app(self):
        app = getattr(self, "app", None)
        return app or self._metadata.searchinfo.app

    def map(self, records):
        for r in records:
            yield r

    def reduce(self, records):
        """ Implementation """

        # this could likely be moved into the actual Issue statement.
        try:
            config = fetch_jira(self, session_key=self.get_session_key())
        except Exception as e:
            yield dict(Exception=str(e))
            return

        payload = {}
        payload['configuration'] = config
        payload['owner'] = self.get_owner()
        payload['sid'] = self.get_sid()
        payload['app'] = self.get_app()

        results = []
        for record in records:
            results.append(record)

        payload['session_key'] = self.get_session_key()

        new_issue = NewIssue(payload)

        if self.send:
            ticket, status = submit_issue(new_issue)
        else:
            ticket, status = None, "Not Sent"

        row = dict()
        if ticket:
            row['ticket'] = ticket.key
        row['status'] = status
        row.update(config)
        row.pop("jira_password")
        yield row

dispatch(JiraCreateCommand, sys.argv, sys.stdin, sys.stdout, __name__)
