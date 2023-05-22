from num2words import num2words


def expand(dateobject):
    """Given a date object, returns a specially formatted string representing it w/ the weekday"""
    return dateobject.strftime(f'%A, %B {dateobject.day}{num2words(dateobject.day, ordinal=True)}, %Y')


def expand_no_weekday(dateobject):
    """Given a date object, returns a specially formatted string representing it w/o the weekday"""
    return dateobject.strftime(f'%B {dateobject.day}{num2words(dateobject.day, ordinal=True)}, %Y')


def auto_expand(dateobject, text):
    """
    If some text does not contain the weekday, generate a datestamp
    that *does* contain the weekday. If the text contains it, the
    datestamp should not contain it
    """
    if dateobject.strftime('%A') not in text:
        return expand(dateobject)
    else:
        return expand_no_weekday(dateobject)
