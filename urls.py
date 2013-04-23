from django.conf.urls import patterns, include, url
from django.views.generic.simple import direct_to_template
from django.contrib.auth.views import login, logout
 

urlpatterns = patterns('VsoilMap.views',
    # Examples:
    # url(r'^$', 'my_blog.views.home', name='home'),
    url(r'nn', 'index', name='index'),
    url(r'^$', 'index', name='index'),
    url(r'^mapper', 'map_vsoil', name='map_vsoil'),
    url(r'^popup', 'pop_up', name='pop'),
    url(r'^insert', 'bulk_import', name='bulk_import'),
    url(r'^edit', 'edit', name='edit'),
    url(r'^my_edits', 'my_edits', name='my_edits'),
    url(r'^my_uploads', 'my_uploads', name='my_uploads'),
    
    #url(r'^contact', direct_to_template, {'template': 'contact.html'}),
)

urlpatterns += patterns('',
    #url(r'^login', 'django.contrib.auth.views.login', {'template_name': 'login.html'}),
    url(r'^logout', 'django.contrib.auth.views.logout',{'next_page':'/vsoilmap/?next=mapper'}),
)



