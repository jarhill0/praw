"""Provide the Reason class."""
from typing import Any, Dict, Generator, Optional, TypeVar

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
    ``created_utc``         Time the submission was created, represented in
                            `Unix Time`_.
    ``description``         The description of the rule, if provided, otherwise
                            a blank string.
    ``kind``                The kind of rule. Can be `submission`, `comment`,
                            or `all`.
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
        short_name: str,
        _data: Optional[Dict[str, Any]] = None,
    ):
        """Construct an instance of the Rule object."""
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

        To delete ``No spam`` from the subreddit ``NAME`` try:

        .. code-block:: python

           reddit.subreddit('NAME').rule['No spam'].delete()

        """
        data = {"r": str(self.subreddit), "short_name": self.short_name}
        self.subreddit._reddit.post(
            API_PATH["remove_subreddit_rule"], data=data
        )

    def update(
        self,
        description: Optional[str] = None,
        kind: Optional[str] = None,
        short_name: Optional[str] = None,
        violation_reason: Optional[str] = None,
    ):
        """Update the rule from this subreddit.

        .. note:: If values are not specified, the existing values will be used
            to update the rule.

        :param description: The new description for the rule. Can be empty.
        :param kind: The kind of item that the rule applies to. One of
            ``submission``, ``comment``, or ``all``.
        :param short_name: The name of the rule.
        :param violation_reason: The reason that is shown on the report menu.

        To update ``No spam`` from the subreddit ``NAME`` try:

        .. code-block:: python

           reddit.subreddit('NAME').removal_reasons['No spam'].update(
               description='Don't do this!',
               violation_reason="Spam post')

        """
        data = {"r": str(self.subreddit), "old_short_name": self.short_name}
        for name, value in {
            "description": description,
            "kind": kind,
            "short_name": short_name,
            "violation_reason": violation_reason,
        }.items():
            data[name] = getattr(self, name) if value is None else value
        updated_rule = self.subreddit._reddit.post(
            API_PATH["update_subreddit_rule"], data=data
        )
        self.__dict__.update(updated_rule.__dict__)


class SubredditRules:
    """Provide a set of functions to a Subreddit's rules."""

    def __getitem__(self, short_name: str) -> Rule:
        """Lazily return the Rule for the subreddit with short_name ``short_name``.

        :param short_name: The short_name of the rule

        This method is to be used to fetch a specific rule, like so:

        .. code-block:: python

           rule_name = 'No spam'
           rule = reddit.subreddit('NAME').rules[rule_name]
           print(rule)

        """
        return Rule(self.subreddit._reddit, self.subreddit, short_name)

    def __init__(self, subreddit: Subreddit):
        """Create a SubredditRules instance.

        :param subreddit: The subreddit whose rules to work with.

        """
        self.subreddit = subreddit
        self._reddit = subreddit._reddit

    def __iter__(self) -> Generator[Rule, None, None]:
        """Return a list of rules for the subreddit.

        This method is used to discover all rules for a subreddit:

        .. code-block:: python

           for rule in reddit.subreddit('NAME').rules:
               print(rule)

        """
        return self.subreddit._reddit.get(
            API_PATH["rules"].format(subreddit=self.subreddit)
        )

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
            ``submission``, ``comment``, or ``all``.
        :param description: The description for the rule. Optional.
        :param violation_reason: The reason that is shown on the report menu.
            If a violation reason is not specified, the short name will be used
            as the violation reason.
        :returns: The Rule added.

        To add rule ``No spam`` to the subreddit ``NAME`` try:

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
        return self.subreddit._reddit.post(
            API_PATH["add_subreddit_rule"], data=data
        )
