# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#     * Rearrange models' order
#     * Make sure each model has one field with primary_key=True
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'
# into your database.


from django.db import models
from django import forms
from django.contrib.auth.models import User

class Cpt(models.Model):
    id = models.IntegerField(primary_key=True)
    date = models.DateTimeField()
    x = models.FloatField() # This field type is a guess.
    y = models.FloatField() # This field type is a guess.
    zmax = models.FloatField() # This field type is a guess.
    zmin = models.FloatField() # This field type is a guess.
    file = models.CharField(max_length=250) # This field type is a guess.
    vsoil_id = models.IntegerField(null=True, blank=True)
    latitude = models.FloatField() # This field type is a guess.
    longitude = models.FloatField() # This field type is a guess.
    name = models.CharField(max_length=250, blank=True) # This field type is a guess.

    class Meta:
        db_table = u'cpt'

class Soiltypes(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=250) # This field type is a guess.
    description = models.CharField(max_length=250,blank=True) # This field type is a guess.
    source = models.CharField(max_length=250,blank=True) # This field type is a guess.
    ydry = models.FloatField(blank=True) # This field type is a guess.
    ysat = models.FloatField(blank=True) # This field type is a guess.
    c = models.FloatField(blank=True) # This field type is a guess.
    phi = models.FloatField(blank=True) # This field type is a guess.
    upsilon = models.FloatField(blank=True) # This field type is a guess.
    k = models.FloatField(blank=True) # This field type is a guess.
    mc_upsilon = models.FloatField(db_column=u'MC_upsilon', blank=True) # Field name made lowercase. This field type is a guess.
    mc_e50 = models.FloatField(db_column=u'MC_E50', blank=True) # Field name made lowercase. This field type is a guess.
    hs_e50 = models.FloatField(db_column=u'HS_E50', blank=True) # Field name made lowercase. This field type is a guess.
    hs_eoed = models.FloatField(db_column=u'HS_Eoed', blank=True) # Field name made lowercase. This field type is a guess.
    hs_eur = models.FloatField(db_column=u'HS_Eur', blank=True) # Field name made lowercase. This field type is a guess.
    hs_m = models.FloatField(db_column=u'HS_m', blank=True) # Field name made lowercase. This field type is a guess.
    ssc_lambda = models.FloatField(db_column=u'SSC_lambda', blank=True) # Field name made lowercase. This field type is a guess.
    ssc_kappa = models.FloatField(db_column=u'SSC_kappa', blank=True) # Field name made lowercase. This field type is a guess.
    ssc_mu = models.FloatField(db_column=u'SSC_mu', blank=True) # Field name made lowercase. This field type is a guess.
    cp = models.FloatField(db_column=u'Cp', blank=True) # Field name made lowercase. This field type is a guess.
    cs = models.FloatField(db_column=u'Cs', blank=True) # Field name made lowercase. This field type is a guess.
    cap = models.FloatField(db_column=u'Cap', blank=True) # Field name made lowercase. This field type is a guess.
    cas = models.FloatField(db_column=u'Cas', blank=True) # Field name made lowercase. This field type is a guess.
    cv = models.FloatField(blank=True) # This field type is a guess.
    color = models.CharField(max_length=250,blank=True) # This field type is a guess.

    class Meta:
        db_table = u'soiltypes'

class SqliteStat1(models.Model):
    tbl = models.TextField(blank=True) # This field type is a guess.
    idx = models.TextField(blank=True) # This field type is a guess.
    stat = models.TextField(blank=True) # This field type is a guess.
    class Meta:
        db_table = u'sqlite_stat1'

class Vsoil(models.Model):
    id = models.IntegerField(primary_key=True)
    x = models.FloatField() # Lars: Changed to float
    y = models.FloatField() # Lars: Changed to float
    latitude = models.FloatField() # Lars: Changed to float
    longitude = models.FloatField() # Lars: Changed to float
    source = models.CharField(max_length=250) # This field type is a guess.
    data = models.TextField() # Lars: Changed to Text
    name = models.CharField(max_length=250,blank=True) # This field type is a guess.
    
 
    class Meta:
        db_table = u'vsoil'

class TrackEdits(models.Model):
    '''
    Small model to save changes a user made to the database.
    Uses the built-in User object as a foreign key.
    '''
    user = models.ForeignKey(User)
    edit = models.TextField()
    date = models.DateTimeField(auto_now_add=True, blank=True)

class TrackUploads(models.Model):
    '''
    Small model to keep track of uploads.
    Uses the built-in User object as a foreign key.
    '''
    user = models.ForeignKey(User)
    upload = models.CharField(max_length=100)
    date = models.DateTimeField(auto_now_add=True, blank=True)



class VsoilForm(forms.ModelForm):
    '''
    Class to auto generate the HTML form for an vsoil entry. The ID is immutable so by
    default excluded from the form. 
    '''

    class Meta:
        model = Vsoil
        exclude = ['id']
        


    def __init__(self, readonly_form=False, *args, **kwargs):
        '''
        Child class to set the fields to 'readonly' if a user doesn't have the permission
        to edit entries.
        '''
        super(VsoilForm, self).__init__(*args, **kwargs)
        f_names = Vsoil._meta.get_all_field_names()
        f_names.remove('id')
        
        if readonly_form:
            for field in f_names:
                self.fields[field].widget.attrs['disabled'] = True
        

class UploadFileForm(forms.Form):
    '''
    Class to auto generate the HTML form for a file upload
    '''
    
    file = forms.FileField()