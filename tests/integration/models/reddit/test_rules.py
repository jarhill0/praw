from unittest import mock
import pytest

from praw.models import Rule

from ... import IntegrationTest


class TestRule(IntegrationTest):
    @property
    def subreddit(self):
        return self.reddit.subreddit(pytest.placeholders.test_subreddit)

    def test_add_rule(self):
        self.reddit.read_only = False
        with self.recorder.use_cassette("TestRule.test_add_rule"):
            rule = self.subreddit.rules.add(
                "PRAW Test",
                "all",
                description="Test by PRAW",
                violation_reason="PTest",
            )
            assert rule.short_name == "PRAW Test"
            assert rule.kind == "all"
            assert rule.description == "Test by PRAW"
            assert rule.violation_reason == "PTest"

    def test_add_rule_without_violation_reason(self):
        self.reddit.read_only = False
        with self.recorder.use_cassette(
            "TestRule.test_add_rule_without_violation_reason"
        ):
            rule = self.subreddit.rules.add("PRAW Test 2", "comment")
            assert rule.short_name == "PRAW Test 2"
            assert rule.kind == "comment"
            assert rule.description == ""
            assert rule.violation_reason == "PRAW Test 2"

    @mock.patch("time.sleep", return_value=None)
    def test_delete_rule(self, _):
        self.reddit.read_only = False
        with self.recorder.use_cassette("TestRule.test_delete_rule"):
            rule = self.subreddit.rules[-1]
            rule.delete()

    def test_get_rules(self):
        with self.recorder.use_cassette("TestRule.test_get_rules"):
            for rule in self.subreddit.rules:
                assert isinstance(rule, Rule)

    def test_get_rule_string(self):
        with self.recorder.use_cassette("TestRule.test_get_rule_string"):
            rule = self.subreddit.rules["PRAW Test"]
            assert isinstance(rule, Rule)
            assert rule.short_name == "PRAW Test"

    def test_get_rule_int(self):
        with self.recorder.use_cassette("TestRule.test_get_rule_int"):
            assert isinstance(self.subreddit.rules[0], Rule)

    def test_get_rule_negative_int(self):
        with self.recorder.use_cassette("TestRule.test_get_rule_int"):
            assert isinstance(self.subreddit.rules[-1], Rule)

    @mock.patch("time.sleep", return_value=None)
    def test_reorder_rules(self, _):
        self.reddit.read_only = False
        with self.recorder.use_cassette("TestRule.test_reorder_rules"):
            rule_list = list(self.subreddit.rules)
            reordered = rule_list[2:3] + rule_list[0:2] + rule_list[3:]
            rule_info = {rule.short_name: rule for rule in rule_list}
            self.subreddit.rules.reorder(reordered)
            for rule in self.subreddit.rules:
                assert rule_info[rule.short_name] == rule

    @mock.patch("time.sleep", return_value=None)
    def test_reorder_rules_no_reorder(self, _):
        self.reddit.read_only = False
        with self.recorder.use_cassette(
            "TestRule.test_reorder_rules_no_reorder"
        ):
            rule_list = list(self.subreddit.rules)
            assert self.subreddit.rules.reorder(rule_list) == rule_list

    @mock.patch("time.sleep", return_value=None)
    def test_update_rule(self, _):
        self.reddit.read_only = False
        with self.recorder.use_cassette("TestRule.test_update_rule"):
            rule = self.subreddit.rules[0]
            rule2 = rule.update(
                description="Updated rule",
                kind="link",
                violation_reason="PUpdate",
            )
            assert rule.description != rule2.description
            assert rule2.description == "Updated rule"
            assert rule.kind != rule2.kind
            assert rule2.kind == "link"
            assert rule.violation_reason != rule2.violation_reason
            assert rule2.violation_reason == "PUpdate"

    @mock.patch("time.sleep", return_value=None)
    def test_update_rule_short_name(self, _):
        self.reddit.read_only = False
        with self.recorder.use_cassette(
            "TestRule.test_update_rule_short_name"
        ):
            rule = self.subreddit.rules[1]
            rule2 = rule.update(
                short_name="PRAW Update",
                description="Updated rule",
                kind="comment",
                violation_reason="PUpdate",
            )
            assert rule != rule2
            assert rule2.short_name == "PRAW Update"
            assert rule.description != rule2.description
            assert rule2.description == "Updated rule"
            assert rule.kind != rule2.kind
            assert rule2.kind == "comment"
            assert rule.violation_reason != rule2.violation_reason
            assert rule2.violation_reason == "PUpdate"

    @mock.patch("time.sleep", return_value=None)
    def test_update_rule_no_params(self, _):
        self.reddit.read_only = False
        with self.recorder.use_cassette("TestRule.test_update_rule_no_params"):
            rule = self.subreddit.rules[1]
            rule2 = rule.update()
            for attr in (
                "created_utc",
                "description",
                "kind",
                "priority",
                "short_name",
                "subreddit",
                "violation_reason",
            ):
                assert getattr(rule, attr) == getattr(rule2, attr)
