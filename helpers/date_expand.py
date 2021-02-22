import datetime

def ordinal(day):
    '''
    Get the ordinal indicator for a day of the month
    '''
    indicators = {1:'st',2:'nd',3:'rd',21:'st',22:'nd',23:'rd',31:'st'}
    if day in indicators: return indicators[day]
    else:                 return 'th'

def expand(dateobject):
    '''Given a date object, returns a specially formatted string representing it w/ the weekday'''
    return dateobject.strftime(f'%A, %B {dateobject.day}{ordinal(dateobject.day)}, %Y')

def expand_no_weekday(dateobject):
    '''Given a date object, returns a specially formatted string representing it w/o the weekday'''
    return dateobject.strftime(f'%B {dateobject.day}{ordinal(dateobject.day)}, %Y')

def auto_expand(dateobject, text):
    '''
    If some text does not contain the weekday, generate a datestamp
    that *does* contain the weekday. If the text contains it, the
    datestamp should not contain it
    '''
    if dateobject.strftime('%A') not in text:
        return expand(dateobject)
    else:
        return expand_no_weekday(dateobject)