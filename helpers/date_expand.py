def ordinal(n):
    """Returns an ordinal string for a number (e.g., 2 -> '2nd')"""
    suffix = ['th', 'st', 'nd', 'rd', 'th', 'th', 'th', 'th', 'th', 'th']
    if 10 <= n < 20:
        return str(n) + 'th'
    else:
        return str(n) + suffix[n % 10]


def expand(dateobject):
    """Given a date object, returns a specially formatted string representing it w/ the weekday"""
    day_as_ordinal = ordinal(dateobject.day)
    return dateobject.strftime(f'%A, %B {day_as_ordinal}, %Y')


def expand_no_weekday(dateobject):
    """Given a date object, returns a specially formatted string representing it w/o the weekday"""
    day_as_ordinal = ordinal(dateobject.day)
    return dateobject.strftime(f'%B {day_as_ordinal}, %Y')


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
