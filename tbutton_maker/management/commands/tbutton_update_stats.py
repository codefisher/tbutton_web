import datetime
from collections import Counter
from operator import itemgetter
from django.http import QueryDict
from django.core.management.base import BaseCommand
from tbutton_web.tbutton_maker.models import UpdateSession
from tbutton_web.tbutton_maker.views import locale_str_getter

class Command(BaseCommand):
    help = 'Dumps out some stats about the tbutton update stats'

    def handle(self, days=7, *args, **options):
        locale_str = locale_str_getter(None)

        time = datetime.datetime.now() - datetime.timedelta(days)
        updates = UpdateSession.objects.filter(time__gt=time)
        count = updates.count()
        print("There were a total of {} hits to the update script.\nThat is {} per day".format(count, count//days))

        counts = Counter()
        for row in updates:
            query = QueryDict(row.query_string)
            counts.update(query.getlist('button'))

        for button_id, count in reversed(sorted(counts.items(), key=itemgetter(1))):
            try:
                print("{} {} {}".format(locale_str('label', button_id), button_id, count/days))
            except:
                pass