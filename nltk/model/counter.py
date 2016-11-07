# Natural Language Toolkit: Language Model Counters
#
# Copyright (C) 2001-2016 NLTK Project
# Author: Ilia Kurenkov <ilia.kurenkov@gmail.com>
# URL: <http://nltk.org/>
# For license information, see LICENSE.TXT

from __future__ import unicode_literals
from collections import Counter, defaultdict
from copy import copy
from itertools import chain

from nltk.probability import FreqDist, ConditionalFreqDist
from nltk import compat

from nltk.model.util import check_ngram_order


def build_vocabulary(cutoff, *texts):
    combined_texts = chain(*texts)
    return NgramModelVocabulary(combined_texts, unk_cutoff=cutoff)


def count_ngrams(order, vocabulary, *training_texts, **counter_kwargs):
    counter = NgramCounter(order, vocabulary, **counter_kwargs)
    for text in training_texts:
        counter.train_counts(text)
    return counter


@compat.python_2_unicode_compatible
class NgramModelVocabulary(Counter):
    """Stores language model vocabulary.

    Satisfies two common language modeling requirements for a vocabulary:
    - When checking membership and calculating its size, filters items by comparing
      their counts to a cutoff value.
    - Adds 1 to its size so as to account for "unknown" tokens.
    """

    def __init__(self, *counter_args, **vocab_kwargs):
        super(self.__class__, self).__init__(*counter_args)
        self.cutoff = vocab_kwargs.pop("unk_cutoff", 1)
        self.unk_label = vocab_kwargs.pop("unk_label", "<UNK>")

    @property
    def cutoff(self):
        return self._cutoff

    @cutoff.setter
    def cutoff(self, new_cutoff):
        if new_cutoff < 1:
            msg_template = "Cutoff value cannot be less than 1. Got: {0}"
            raise ValueError(msg_template.format(new_cutoff))
        self._cutoff = new_cutoff

    def mask_oov(self, word):
        """Replaces out-of-vocabulary word with unk_label.

        Words with counts less than cutoff, aren't in the vocabulary.
        :param: word
        """
        return word if word in self else self.unk_label

    def __contains__(self, item):
        """Only consider items with counts GE to cutoff as being in the vocabulary."""
        return self[item] >= self.cutoff

    def __iter__(self):
        """Building on membership check define how to iterate over vocabulary."""
        parent_iter = super(self.__class__, self).__iter__()
        # During copying/instantiation Python calls this before we have
        # a chance to add the "unk_label" attribute to the object.
        # In those cases we fall back to Counter's __iter__ implementation.
        if getattr(self, "unk_label", None) is None:
            return parent_iter
        return chain((item for item in parent_iter if item in self),
                     [self.unk_label])

    def __len__(self):
        """Computing size of vocabulary reflects the cutoff."""
        return sum(1 for item in self)

    def __eq__(self, other):
        return (super(self.__class__, self).__eq__(other)
                and (self.cutoff == other.cutoff))

    def __ne__(self, other):
        return not self.__eq__(other)

    def __copy__(self):
        new = self.__class__(self)
        new.__dict__.update(self.__dict__)
        return new


@compat.python_2_unicode_compatible
class NgramCounter(object):
    """Class for counting ngrams"""

    def __init__(self, order, vocabulary, unk_cutoff=None, unk_label="<UNK>"):
        """
        :type training_text: List[List[str]]
        """
        self.order = check_ngram_order(order)
        self.unk_label = unk_label

        # Set up the vocabulary
        self._set_up_vocabulary(vocabulary, unk_cutoff)

        self._ngram_orders = defaultdict(ConditionalFreqDist)
        self.unigrams = FreqDist()

    def _set_up_vocabulary(self, vocabulary, unk_cutoff):
        self.vocabulary = copy(vocabulary)  # copy needed to prevent state sharing
        if unk_cutoff is not None:
            # If cutoff value is provided, override vocab's cutoff
            self.vocabulary.cutoff = unk_cutoff

    def _enumerate_ngram_orders(self):
        return enumerate(range(self.order, 1, -1))

    def train_counts(self, training_text):
        # Note here "1" indicates an empty vocabulary!
        # See NgramModelVocabulary __len__ method for more.
        if len(self.vocabulary) <= 1:
            raise ValueError("Cannot start counting ngrams until "
                             "vocabulary contains more than one item.")

        for sent in training_text:
            sent_start = True
            for ngram in sent:
                if len(ngram) > self.order:
                    raise ValueError("Ngram larger than highest order: "
                                     "{0}".format(ngram))
                context, word = tuple(ngram[:-1]), ngram[-1]

                if sent_start:
                    for context_word in context:
                        self.unigrams[context_word] += 1
                    sent_start = False

                for trunc_index, ngram_order in self._enumerate_ngram_orders():
                    trunc_context = context[trunc_index:]
                    # note that above line doesn't affect context on first iteration
                    self[ngram_order][trunc_context][word] += 1
                self.unigrams[word] += 1

    def __getitem__(self, order_number):
        """For convenience allow looking up ngram orders directly here."""
        order_number = check_ngram_order(order_number, max_order=self.order)
        if order_number == 1:
            return self.unigrams
        return self._ngram_orders[order_number]
