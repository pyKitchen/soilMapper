'''
Small module to extract new entries for the vsoil model from a text file.

Dependencies: projections.py to convert the xy coordinates to WSG84

Written 04-2013 by Lars Claussen @ pyKitchen
'''


from VsoilMap.projections import FromRD

class ImportVSoilFromText(object):
    '''
    Base class that handles the data extraction. Methods:
    read_data >> reads data from file as is
    get_profiles >> make the data available per profile 
    '''
        
        
    def __init__(self):
        self


    def read_data(self, file_in):
        '''
        file handling
        '''

        if file_in is None:
            raise Exception("No file passed to read_data()")

        else:
            
            try:
                with open(file_in, 'r') as f:
                    self.data = f.read()
            except IOError, ierr:
                print "%s \n couldn't read file in method read_data()"  % (ierr,)


    def get_profiles(self,raw_data):
        '''
        data handling
        '''
        
        # '#' is used as a delimiter for the profiles
        p = raw_data.split('#')
        
        # check if the first list element is a whitespace. 
        if p[0] is '':           
            p.pop(0)

        self.attributes = []
        for e in p:
            l_elem = e.split('\n')
            if '' in l_elem:
                l_elem.remove('')
            # call class 'Profile()' on all list elements to assign the attributes to the object    
            a = Profile(l_elem)
            self.attributes.append(a)



class Profile (object):
    '''helper class to assign the attributes to the ImportVSoilFromText-object.
    This class is called from ImportVSoilFromText-method 'get_profiles'.
    The attributes  correspond with the model fields of vsoil (name, x, y, lat, long, data_txt)
    '''

    def __init__(self, l_elem):
        # not necessary but better double check for whitespaces...
        if '' in l_elem:
            l_elem.remove('')
        self.name = l_elem[0]
        xy = l_elem[1].split(';')
        self.x = xy[0]
        self.y = xy[1]
        
        f = FromRD()
        self.lat, self.lon  = f.RD_2_WGS84(float(self.x),float(self.y))
        

        data_block = []
        # skip the first 2 elements (which are 'name' and 'xy')
        for i in xrange(2,len(l_elem)):
            # soil compostion has to have this format: start height; stop height; code id
            # split and make elements available by index
            try:
                z_info = l_elem[i].split(';')
                    
            except AttributeError,aErr:
                raise str(aErr)
            
            # only the first row has three elements...    
            if len(z_info) == 3:  
                start_z = z_info[0]
                stop_z = z_info[1]
                id_stype = z_info[2]
            
            #...stop height is start height of following layer    
            else:
                start_z = stop_z
                stop_z = z_info[0]
                id_stype = z_info[1]
            data_block.append([start_z,stop_z, '\t' + id_stype])

        # first join by ';', then make a single string 
        joind_layer = [';'.join(e for e in seq) for seq in data_block]
        self.data_txt = '\n'.join(layer for layer in joind_layer)        
        
        
if __name__ == '__main__':
    '''
    example usage
    '''
    
    path = '/Users/larsvegas/Desktop'
    f = '/vsoil_in_test.txt'
    
    
    import_obj = ImportVSoilFromText()
    import_obj.read_data(path+f)
    data = import_obj.data
    import_obj.get_profiles(data)
    list_x = [float(a.x) for a in import_obj.attributes]

