"""URL Configuration for kck_project."""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve as static_serve

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('services/', include('services.urls', namespace='services')),
    path('events/', include('events_app.urls', namespace='events')),
    path('community/', include('community.urls', namespace='community')),
    path('leaders/', include('leaders.urls', namespace='leaders')),
    path('certificates/', include('certificates.urls', namespace='certificates')),
    path('communications/', include('communications.urls', namespace='communications')),
    path('embassy-services/', include('embassy_liaison.urls', namespace='embassy_liaison')),
    path('endorsements/', include('endorsements.urls', namespace='endorsements')),
    path('market/', include('market.urls', namespace='market')),
    path('membership/', include('memberships.urls', namespace='memberships')),
    path('portal/', include('portal.urls', namespace='portal')),
    path('', include('core.urls', namespace='core')),
]

# Serve user-uploaded media files regardless of DEBUG setting.
# (Static files are served by WhiteNoise. In a production setup behind
# nginx/apache, the web server should serve /media/ directly — but for a
# single-server dev/staging deployment this keeps uploads visible.)
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', static_serve, {'document_root': settings.MEDIA_ROOT}),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

admin.site.site_header = 'KCK Administration'
admin.site.site_title = 'KCK Admin'
admin.site.index_title = 'Kenya Community in Korea - Admin Panel'

# Custom error handlers
handler404 = 'core.views.custom_404'
handler500 = 'core.views.custom_500'
handler403 = 'core.views.custom_403'
handler400 = 'core.views.custom_400'
