import re

class PreProcess:
    def __init__(self, stopwords_):
        self.STOPWORDS = stopwords_
        self.STATE_ABBR = [
            "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS",
            "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC",
            "ND", "OH", "OK", "OR", "PA", "PR", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "VI", "WA", "WV",
            "WI", "WY",
        ]
        self.STATE_ABBR = [r"\b" + x.lower() + r"\b" for x in self.STATE_ABBR]

        # Regex patterns used in GPT cleaner
        self.short_digits_re = re.compile(r"\b(\d{1,3})\b")
        self.four_digits_re = re.compile(r"\b(\d{4})\b")
        self.long_digits_re = re.compile(r"\b([a-z]*\d{5,17}\w*)\b")
        self.extremely_long_digits_re = re.compile(r"\b([a-z]*\d{18,}\w*)\b")
        self.mixed_long_digits_re = re.compile(r"\b(([a-z]*[0-9]){3,}\w*)\b")
        self.long_word_with_numbers_re = re.compile(r"\b(?=\w*[^\W\d_])(?=\w*\d)\w{9,}\b")
        self.conf_number_re = re.compile(r"\b(conf#?:?\s?[a-z0-9]+)\b")
        self.single_char_re = re.compile(r"\b\w\b")
        self.star_re = re.compile(r"\*")

    def clean_description_GPT_knowledge_base(self, text: str) -> str:
        # Split word by capital letter
        text = " ".join(
            " ".join(re.findall(r"[A-Z]+[^A-Z]*", x)) if x[0].isupper() else x
            for x in text.split()
        )
        # Lowercase
        text = text.lower()

        # Remove short and long digit patterns
        text = self.short_digits_re.sub(" ", text)
        text = self.four_digits_re.sub(" ", text)
        text = self.long_digits_re.sub(" ", text)
        text = self.mixed_long_digits_re.sub(" ", text)
        text = self.long_word_with_numbers_re.sub(" ", text)
        text = self.conf_number_re.sub(" ", text)
        text = self.extremely_long_digits_re.sub(" ", text)
        text = self.single_char_re.sub(" ", text)
        text = self.star_re.sub(" ", text)

        # Replace state abbreviations
        text = re.sub("|".join(self.STATE_ABBR), " StateAbbr ", text)

        # Handle empty or stopword-only cases
        if (
            len(text) == 0
            or sum([x not in self.STOPWORDS for x in text.lower().split()]) == 0
        ):
            text = "NO DESCRIPTION"
        return text
