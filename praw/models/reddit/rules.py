"""Provide the Rule class."""
from json import loads
from typing import Dict, Generator, List, Optional, TypeVar, Union
from urllib.parse import quote

from ...const import API_PATH
from ...exceptions import ClientException
from .base import RedditBase

_Rule = TypeVar("_Rule")
Reddit = TypeVar("Reddit")
Subreddit = TypeVar("Subreddit")


class Rule(RedditBase):
    """An individual Rule object.

    **Typical Attributes**

    This table describes attributes that typically belong to objects of this
    class. Since attributes are dynamically provided (see
    :ref:`determine-available-attributes-of-an-object`), there is not a
    guarantee that these attributes will always be present, nor is this list
    necessarily comprehensive.

    ======================= ===================================================
    Attribute               Description
    ======================= ===================================================
    ``created_utc``         Time the rule was created, represented in
                            `Unix Time`_.
    ``description``         The description of the rule, if provided, otherwise
                            a blank string.
    ``kind``                The kind of rule. Can be ``"link"``, ``comment"``,
                            or ``"all"``.
    ``priority``            Represents where the rule is ranked. For example,
                            the first rule is at priority ``0``.
    ``short_name``          The name of the rule.
    ``violation_reason``    The reason that is displayed on the report menu for
                            the rule.
    ======================= ===================================================


    .. _Unix Time: https://en.wikipedia.org/wiki/Unix_time

    """

    STR_FIELD = "short_name"

    def __init__(
        self,
        reddit: Reddit,
        subreddit: Subreddit,
        short_name: Optional[str] = None,
        _data: Optional[Dict[str, str]] = None,
    ):
        """Construct an instance of the Rule object."""
        if (short_name, _data).count(None) != 1:
            raise ValueError("Either short_name or _data needs to be given.")
        self.short_name = short_name
        self.subreddit = subreddit
        super().__init__(reddit, _data=_data)

    def _fetch(self):
        for rule in self.subreddit.rules:
            if rule.short_name == self.short_name:
                self.__dict__.update(rule.__dict__)
                self._fetched = True
                return
        raise ClientException(
            "r/{} does not have the rule {}".format(
                self.subreddit, self.short_name
            )
        )

    def delete(self):
        """Delete a rule from this subreddit.

        To delete ``"No spam"`` from the subreddit ``"NAME"`` try:

        .. code-block:: python

            reddit.subreddit('NAME').rule['No spam'].delete()

        """
        data = {"r": str(self.subreddit), "short_name": self.short_name}
        self._reddit.post(API_PATH["remove_subreddit_rule"], data=data)

    def update(
        self,
        description: Optional[str] = None,
        kind: Optional[str] = None,
        short_name: Optional[str] = None,
        violation_reason: Optional[str] = None,
    ):
        """Update the rule from this subreddit.

        .. note:: Existing values will be used for any unspecified arguments.

        :param description: The new description for the rule. Can be empty.
        :param kind: The kind of item that the rule applies to. One of
            ``"link"``, ``"comment"``, or ``"all"``.
        :param short_name: The name of the rule.
        :param violation_reason: The reason that is shown on the report menu.

        To update ``"No spam"`` from the subreddit ``"NAME"`` try:

        .. code-block:: python

            reddit.subreddit("NAME").removal_reasons["No spam"].update(
                description="Don't do this!",
                violation_reason="Spam post")

        """
        data = {"r": str(self.subreddit), "old_short_name": self.short_name}
        for name, value in {
            "description": description,
            "kind": kind,
            "short_name": short_name,
            "violation_reason": violation_reason,
        }.items():
            data[name] = getattr(self, name) if value is None else value
        updated_rule = self._reddit.request(
            "POST", API_PATH["update_subreddit_rule"], data=data
        )
        self._reddit._objector.objectify(updated_rule)
        # We want any errors to be passed, but we don't want to use the
        # objected value because it returns a LiveThread.
        rule_data = loads(updated_rule["json"]["data"]["rules"])[0]
        return Rule(self._reddit, self.subreddit, _data=rule_data)


class SubredditRules:
    """Provide a set of functions to a Subreddit's rules."""

    def __getitem__(self, short_name: Union[str, int]) -> Rule:
        """Return the Rule for the subreddit with short_name ``short_name``.

        :param short_name: The short_name of the rule, or the rule number.

        .. note:: Rules fetched using a specific rule name are lazy loaded, so
            you might have to access an attribute to get all of the expected
            attributes.

        This method is to be used to fetch a specific rule, like so:

        .. code-block:: python

            rule_name = 'No spam'
            rule = reddit.subreddit('NAME').rules[rule_name]
            print(rule)

        You can also fetch a numbered rule of a subreddit.

        Rule numbers start at ``0``, so the first rule is at index ``0``, and the
        second rule is at index ``1``, and so on.

        If a rule of a specific number does not exist, an
        :py:class:`IndexError` will be thrown.

        .. note:: You can use negative indexes, such as ``-1``, to get the last rule.

        For example, to fetch the second rule of ``AskReddit``:

        .. code-block:: python

            rule = reddit.subreddit("AskReddit").rules[1]

        """
        if isinstance(short_name, int):
            return list(self)[short_name]
        return Rule(self._reddit, self.subreddit, short_name)

    def __init__(self, subreddit: Subreddit):
        """Create a SubredditRules instance.

        :param subreddit: The subreddit whose rules to work with.

        """
        self.subreddit = subreddit
        self._reddit = subreddit._reddit

    def __iter__(self) -> Generator[Rule, None, None]:
        """Return a list of rules for the subreddit.

        :returns: A generator containing all of the rules of a subreddit.

        This method is used to discover all rules for a subreddit:

        .. code-block:: python

           for rule in reddit.subreddit('NAME').rules:
               print(rule)

        """
        for rule in self._make_rule_list(
            self._reddit.get(
                API_PATH["rules"].format(subreddit=self.subreddit)
            )["rules"]
        ):
            yield rule

    def _make_rule(self, data: Dict[str, str]) -> Rule:
        """Make a rule object from a data dict.

        :param data: The dictionary of attributes and values
        :returns: An instance of :class:`.Rule`.
        """
        return Rule(self._reddit, self.subreddit, _data=data)

    def _make_rule_list(self, data_list: List[Dict[str, str]]) -> List[Rule]:
        """Convert a list of rule dicts to Rule objects.

        :param data_list: The list of dictionaries
        :returns: A list of instances of :class:`.Rule`.
        """
        return [self._make_rule(ruledata) for ruledata in data_list]

    def add(
        self,
        short_name: str,
        kind: str,
        description: str = "",
        violation_reason: Optional[str] = None,
    ) -> Rule:
        """Add a removal reason to this subreddit.

        :param short_name: The name of the rule.
        :param kind: The kind of item that the rule applies to. One of
            ``"link"``, ``"comment"``, or ``"all"``.
        :param description: The description for the rule. Optional.
        :param violation_reason: The reason that is shown on the report menu.
            If a violation reason is not specified, the short name will be used
            as the violation reason.
        :returns: The Rule added.

        To add rule ``"No spam"`` to the subreddit ``"NAME"`` try:

        .. code-block:: python

           reddit.subreddit('NAME').rules.add(
               "No spam",
               "all",
               description="Do not spam. Spam bad")

        """
        data = {
            "r": str(self.subreddit),
            "description": description,
            "kind": kind,
            "short_name": short_name,
            "violation_reason": short_name
            if violation_reason is None
            else violation_reason,
        }
        request_data = self._reddit.request(
            "POST", API_PATH["add_subreddit_rule"], data=data
        )
        self._reddit._objector.objectify(request_data)
        # We want any errors to be passed, but we don't want to use the
        # objected value because it returns a LiveThread.
        return self._make_rule(loads(request_data["json"]["data"]["rules"])[0])

    def reorder(self, rule_list: List[Rule]) -> List[Rule]:
        """Reorder the rules of a subreddit.

        :param rule_list: The list of rules, in the wanted order. Each index of
            the list indicates the position of the rule.
        :returns: A list containing the rules in the specified order.

        For example, to move the fourth rule to the first position, and then to
        move the prior first rule to where the third rule originally was:

        .. code-block:: python

            subreddit = reddit.subreddit("subreddit")
            rules = list(subreddit.rules)
            new_rules = rules[3:4] + rules[1:3] + rules[0:1] + rules[4:]
            # Alternate: [rules[3]] + rules[1:3] + [rules[0]] + rules[4:]
            new_rule_list = subreddit.rules.reorder(new_rules)

        """
        order_string = quote(
            ",".join([str(item) for item in rule_list]), safe=","
        )
        data = {"r": str(self.subreddit), "new_rule_order": order_string}
        request_data = self._reddit.request(
            "POST", API_PATH["reorder_subreddit_rules"], data=data
        )
        self._reddit._objector.objectify(request_data)
        # We want any errors to be passed, but we don't want to use the
        # objected value because it returns a LiveThread.
        return self._make_rule_list(
            loads(request_data["json"]["data"]["rules"])
        )
