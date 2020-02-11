import inspect

from django.test import TestCase
from django.test.client import RequestFactory
from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.contrib.auth.models import AnonymousUser

from django_countries import filters
from django_countries.tests import models

test_site = admin.AdminSite(name="test-admin")


class PersonAdmin(admin.ModelAdmin):
    list_filter = [("country", filters.CountryFilter)]


test_site.register(models.Person, PersonAdmin)


class TestCountryFilter(TestCase):
    def get_changelist_kwargs(self):
        m = self.person_admin
        sig = inspect.signature(ChangeList.__init__)
        kwargs = {'model_admin': m}
        for arg in list(sig.parameters)[2:]:
            if hasattr(m, arg):
                kwargs[arg] = getattr(m, arg)
        return kwargs

    def setUp(self):
        models.Person.objects.create(name="Alice", country="NZ")
        models.Person.objects.create(name="Bob", country="AU")
        models.Person.objects.create(name="Chris", country="NZ")
        self.person_admin = PersonAdmin(models.Person, test_site)

    def test_filter_none(self):
        request = RequestFactory().get("/person/")
        request.user = AnonymousUser()
        cl = ChangeList(request, **self.get_changelist_kwargs())
        cl.get_results(request)
        self.assertEqual(list(cl.result_list), list(models.Person.objects.all()))

    def test_filter_country(self):
        request = RequestFactory().get("/person/", data={"country": "NZ"})
        request.user = AnonymousUser()
        cl = ChangeList(request, **self.get_changelist_kwargs())
        cl.get_results(request)
        self.assertEqual(
            list(cl.result_list), list(models.Person.objects.exclude(country="AU"))
        )

    def test_choices(self):
        request = RequestFactory().get("/person/", data={"country": "NZ"})
        request.user = AnonymousUser()
        cl = ChangeList(request, **self.get_changelist_kwargs())
        choices = list(cl.filter_specs[0].choices(cl))
        self.assertEqual(
            [c["display"] for c in choices], ["All", "Australia", "New Zealand"]
        )
        for choice in choices:
            self.assertEqual(choice["selected"], choice["display"] == "New Zealand")
