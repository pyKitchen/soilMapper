# standard libs
import os
import collections
import difflib

# django libs
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.template import RequestContext
from django.utils import simplejson
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User

# project libs
from VsoilMap.models import Vsoil, Soiltypes, VsoilForm, UploadFileForm, TrackEdits, TrackUploads
from VsoilMap.import_vsoil import ImportVSoilFromText
from VsoilMap.bulkops import insert_many

#---------------------------------------------------------------------------------------------------------------------------
#                               Custom classes for the view functions
#---------------------------------------------------------------------------------------------------------------------------


class LoginRequiredDecorator(object):
    '''
    Custom login decorator
    '''
    def __init__(self, orig_func):
        self.orig_func = orig_func

    def __call__(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return self.orig_func(request, *args, **kwargs)
        else:
            #re-direct to the login page (here start page)
            return redirect("/vsoilmap")
    
    
#---------------------------------------------------------------------------------------------------------------------------
#                               View functions
#---------------------------------------------------------------------------------------------------------------------------


def index(request):
    '''
    View for the start/login page 
    '''
    
    state = 'Welkom op de site soilMapper. Please login.'
    next_param = request.GET.get('next', None)
    username = password = ''
    if request.method =='POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                state = "You're successfully logged in!"
                if next_param is None:
                    next_param = 'mapper'
                re_str = '/vsoilmap/%s' % (next_param,)
                return redirect(re_str)                
                
            else:
                state = "Your account is not active, please contact the site admin."
        else:
            state = "Your username and/or password were incorrect."

    return render_to_response('index.html',{'state':next_param, 'username': username},
                              context_instance=RequestContext(request))

    
@LoginRequiredDecorator
def my_edits(request):
    '''
    my edits view. Still under construction but yet works. 
    '''
    
    track_edit_obj = TrackEdits.objects.filter(user=request.user)
    return render_to_response('myedits.html',{'track_edit_obj':track_edit_obj},
                          context_instance=RequestContext(request))
    
@LoginRequiredDecorator
def my_uploads(request):
    '''
    my uploads view. Still under construction but yet works. 
    '''
    
    track_upload_obj = TrackUploads.objects.filter(user=request.user)
    return render_to_response('myedits.html',{'track_edit_obj':track_upload_obj},
                          context_instance=RequestContext(request))
    

@LoginRequiredDecorator
def edit(request):
    '''
    View for edits of DB entries
    '''

    def _obj_look_up(curr_id, perm):
        '''
        helper function to get the next and previous ID's from the DB. Logic is
        implemented in the functions _get_next() and _get_prev(). See section HELPER FUNCTIONS at
        the end of this script
        '''
        
        n = _get_next(curr_id)
        p = _get_prev(curr_id)
        
        # check if the demanded ID exists, otherwise get closest ID
        try:    
            v_obj = Vsoil.objects.get(id=curr_id)
        except:
            close = Vsoil.objects.filter(id__lt=curr_id)
            near_id = close[len(close)-1].id
            v_obj = Vsoil.objects.get(id=near_id)
            
        # return a VsoilForm-object (with instance, read 'with data')
        if perm is True:
            v_form = VsoilForm(instance=v_obj)
        else:
            v_form = VsoilForm(readonly_form=True, instance=v_obj)
        return v_obj, v_form, n, p
        
    

    # called through href. Get instance by ID and pre-populate the form
    if request.method == 'GET':
        perm = _permission_handler(request.user)
        curr_id = int(request.GET['id'])
        v_obj, v_form, n, p = _obj_look_up(curr_id, perm)
        return render_to_response('edit.html',{'obj':v_obj,
                                               'perm':perm,
                                               'next_id':n,
                                               'prev_id':p,
                                               'v_form':v_form},
                              context_instance=RequestContext(request))

    # called through submit with changes applied to the entry
    if request.method == 'POST':
        perm = _permission_handler(request.user)
        post_id = request.POST['id']
        v_obj = Vsoil.objects.get(id=post_id)
        v_form_edited =  VsoilForm(False, request.POST, instance=v_obj)
        
        if v_form_edited.is_valid():
            edited = "edited ID %s: \n%s" % (post_id, v_form_edited) 
            te = TrackEdits(user=request.user,edit=edited)
            te.save()
            v_form_edited.save()
            re_str = '/vsoilmap/popup?id=%s' % (post_id,)
            return redirect(re_str)
            
        else:
            v_obj, v_form, n, p = _obj_look_up(post_id, perm)
            flag = 'form data invalid'
            if perm is False:
                flag = 'no permission to edit'
            return render_to_response('edit.html',{'obj':v_obj,
                                                   'flag':flag,
                                                    'next_id':n,
                                                    'prev_id':p,
                                                    'v_form':v_form},
                              context_instance=RequestContext(request))
            

def create_account(request):
    '''
    NOT IMPLEMENTED. View to let users create an account. 
    '''
    if request.method =='POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            #pass
            user = form.save()
            new_user = authenticate(username=request.POST['username'],
                                    password=request.POST['password1'])
                        
            if new_user is not None:
                if new_user.is_active:
                    login(request, new_user)
                    return render_to_response('welcome.html',
                              {'user': new_user},
                              context_instance=RequestContext(request))
                else:
                    return HttpResponseRedirect("/account/invalid/")
            else:
                return HttpResponseRedirect("/account/error/")
            
            '''
            return render_to_response('welcome.html',
                              #{'user': user},
                              context_instance=RequestContext(request))
            '''
    else:
        form = UserCreationForm()
    
    return render_to_response('create_account.html',
                              {'form': form},
                              context_instance=RequestContext(request))
    
@LoginRequiredDecorator
def map_vsoil(request):
    '''
    View for the web map. 
    '''
    
    # get lat/long/ids from the DB as lists
    lati = Vsoil.objects.values_list('latitude',flat=True)
    longi = Vsoil.objects.values_list('longitude',flat=True)
    ids = Vsoil.objects.values_list('id',flat=True)
    center_index = len(lati)/2
    zoom = [lati[center_index],longi[center_index]]
    
    # create the geojson object
    geo_json = [ {"type": "Feature",
                        "properties": {
                            "id":  ident,
                            "popupContent":  "id=%s" % (ident,) 
                            },
                        "geometry": {
                            "type": "Point",
                            "coordinates": [lon,lat] }}
                        for ident,lon,lat in zip(ids,longi,lati) ] 


    return render_to_response('overview.html',
                              {'geo_json': geo_json,
                               'zoom':zoom},
                              context_instance=RequestContext(request))

@LoginRequiredDecorator
def pop_up(request):
    'View for the data presentation of a single point'
    
    if request.method == 'GET':
        t = request.GET['id']
        fst = Vsoil.objects.get(id=t)
        
        # data: start height; stop height;\t id
        # t_s: ["start height; stop height;", "id",...]
        t_s = fst.data.split()

        # group([0,3,4,10,2,3], 2) => [(0,3), (4,10), (2,3)]
        # ts_g: [("start height; stop height;", "id"),(...)]
        ts_g = group(t_s,2)
        
        series, tab = _stack_data(ts_g)    
        return render_to_response('stacked.html',
                              { 'pnt_obj': fst,
                                'json_data': simplejson.dumps(series),
                               'data':tab},
                              context_instance=RequestContext(request))
        







@LoginRequiredDecorator
def bulk_import(request):
    '''
    File upload view. 
    '''
    
    def _else_handler(msg, flag = 'white'):
        '''
        handles the requests that are not of method POST or where the file upload
        wasn't successful. 
        '''
        
        # check permissions
        perm = _permission_handler(request.user)
        if perm is False:
            flag = 'red'
            msg = 'you don\'t have permission to upload files'
            form_up = ''
        else:
            form_up = UploadFileForm()
        return render_to_response('upload.html',
              {'flag':flag,
                'msg': msg,
               'form_up': form_up },
              context_instance=RequestContext(request))

    if request.method == 'POST':
        form_up = UploadFileForm(request.POST, request.FILES)
        if form_up.is_valid():
            err, list_new_ids = handle_uploaded_file(request.FILES['file'])
            if err == None:
                    # store upload information in DB
                    upl_str = 'Uploaded file:%s. \nNew ID\'s in database are:%s ' % (request.FILES['file'],list_new_ids)
                    tu = TrackUploads(user=request.user, upload=upl_str)
                    tu.save()
                    msg_str = 'Upload complete. Inserted IDs: %s' % (list_new_ids,)
                    return render_to_response('upload.html',
                          {'flag': 'green',
                            'msg': msg_str,
                           'form_up':UploadFileForm() },
                          context_instance=RequestContext(request))
            else:
                return _else_handler(err, flag = 'red')

        else:
            return _else_handler('form is invalid', flag = 'red')

    else:
        return _else_handler('Upload a txt file.')
                
                


#---------------------------------------------------------------------------------------------------------------------------
#                               HELPER FUNCTIONS
#---------------------------------------------------------------------------------------------------------------------------
def _stack_data(ts_g):
    '''
    helper function to organize the data for the stacked bar chart in the popup view.
    '''
    # container for the series dict
    series = []
    
    # container for data displayed in the HTML-table 
    tab = []
    
    start_z = ts_g[0][0].split(';')[0]
    # flip the list get a proper color overlay in the flot chart 
    for i,l in reversed(list(enumerate(ts_g))):
        try:
            s = Soiltypes.objects.get(id=int(l[1]))
        except:
            raise Exception("Couldn't get soiltype\n")
        
        try:
            # split the elements into ["stop height,ID"]
            z = l[0].split(";")
            
            tmp_d = {
                'data': [
                [float(start_z), float(z[1])]
                ],
                'label': str(s.description),
                'color':str(s.color)
                }
            series.append(tmp_d)
            tab.append([z[0],z[1],s.description,s.color])
                
        except Exception:
            raise Exception("couldn't get data from vsoil data field\n")
    
    
    return series, tab.reverse()



def handle_uploaded_file(f):
    '''
    Function to handle file uploads. Does some basic checks on file type, file extension, content type and size.
    It also checks on possible double entries xy-coordinates file vs database. 
    Relies on the ImportVSoilFromText()-object to convert the file into the vsoil model scheme.
    '''

    status_handler ={'clear':None,
                     'size':'File too large. 10MB max',
                     'type':'is not of type text/plain',
                     'tail':'does not have the extension txt',
                     'double':'xy dublicate found in database'}

    #location of the directory uploads. Change according to server config when deploying 
    p = r'/Users/larsvegas/Documents/development/soilMapper/VsoilMap/uploads' 

    # do same checks on the file before proceeding. Size limit 10MB
    if f.size > 10240:      
        return status_handler['size'], None
    if not f.content_type in ['text/plain']:
        return status_handler['type'], None
    if not os.path.splitext(f.name)[1] in ['.txt', '.met']:
        return status_handler['tail'], None
        

    up_f = '%s/%s' % (p,f)
        
    with open(up_f, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)


    # do the data magic. All attributes are avaible through the 'import_obj'     
    import_obj = ImportVSoilFromText()
    import_obj.read_data(up_f)
    data = import_obj.data
    import_obj.get_profiles(data)
    list_x = [float(a.x) for a in import_obj.attributes]
    list_y = [float(a.y) for a in import_obj.attributes]
    
    xy = zip(list_x,list_y)
    
    # are there double entries in the text file?
    u = [a for a, b in collections.Counter(xy).items() if b > 1]
    if u:
        except_str = 'xy dublicate found in upload file:%s' % (u,)
        return except_str, None
    else:
        pass

    # is there a point in the text file that is already present in the DB?
    if _check_uniq('x', xy, opt_extra='y') is False:
        return status_handler['double'], None
    

    
    update_coll = []
    for profiles in import_obj.attributes:
        # filter __gt >> greater than
        all_ids = Vsoil.objects.filter(id__gt=1)
        biggest_id = all_ids[len(all_ids)-1].id 
        newly_needed_ids = len(import_obj.attributes)
        list_new_ids = [ biggest_id + i for i in range(1,newly_needed_ids + 1) ]
        if _check_uniq('id',list_new_ids) is True:
            vs = Vsoil()
            vs.id = biggest_id
            vs.x = profiles.x
            vs.y = profiles.y
            vs.latitude = profiles.lat
            vs.longitude = profiles.lon
            vs.name = profiles.name
            vs.data = profiles.data_txt
            vs.save()
        else:
            except_str = 'one of the following ids exists already in the database: %s' % (list_new_ids,)
            return except_str, None
    
            
    
    return status_handler['clear'],list_new_ids
    
        

def _check_uniq(check_for, seq, opt_extra = None):
    
    
    values = Vsoil.objects.values_list(check_for,flat=True)
    if opt_extra is not None:
        vl_extra = Vsoil.objects.values_list(opt_extra,flat=True)
        values = zip(values, vl_extra)
    s_seq = set(seq)
    print s_seq
    print values
    for s in s_seq:
        if s in values:
            print s
            return False
    return True
        
        
    
'''
def _change_detection(seq, seq2):
    changes = []
    d = difflib.Differ()
    for val_s1, val_s2 in zip(seq.itervalues(),seq2.itervalues()):
        #if str(val_s1) != str(val_s2):
            #ch_str = '%s changed to: %s' % (val_s1, val_s2)
            result = list(d.compare(str(val_s1), str(val_s2)))
            changes.append(result)
    return changes
'''


def _permission_handler(user, perm='VsoilMap.add_soiltypes'):
    '''
    helper funtion. checks for a given user if he/she has the permission
    to 'add soiltypes'. This functions as a synonym for the right to edit
    database entries.
    '''
    u=User.objects.get(username=user)
    
    if perm in  u.get_all_permissions():
        return True
    else:
        return False
        
        

def group(lst, n):
    """group([0,3,4,10,2,3], 2) => [(0,3), (4,10), (2,3)]
        
    Group a list into consecutive n-tuples. Incomplete tuples are
    discarded e.g.
    
    >>> group(range(10), 3)
    [(0, 1, 2), (3, 4, 5), (6, 7, 8)]
    """
    a = zip(*[lst[i::n] for i in range(n)])
    return [list(pair) for pair in a]


def _get_next(current_id):
    '''
    helper function to get the next object from the vsoil table.
    Like this ID's don't have to be continuous. 
    id__gt --> id grEATER than, returns a list
    id__lt --> id leSS than, returns a list
    '''
    
    next_id = Vsoil.objects.filter(id__gt=current_id)
    if next_id:
        return next_id[0].id
    else:
        start_id = Vsoil.objects.filter(id__lt=current_id)
        return start_id[0].id
        
        return False

def _get_prev(current_id):
    '''
    helper function to get the previuous object from the vsoil table.
    Like this ID's don't have to be continuous. 
    id__gt --> id grEATER than, returns a list
    id__lt --> id leSS than, returns a list
    '''
    prev_id = Vsoil.objects.filter(id__lt=current_id)
    if prev_id:
        return prev_id[len(prev_id)-1].id
    else:
        stop_id = Vsoil.objects.filter(id__gt=current_id)
        return stop_id[len(stop_id)-1].id
        


    

    
