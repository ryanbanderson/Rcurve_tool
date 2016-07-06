import arcpy
import pythonaddins
import os
import numpy as np

#Set the shapefile to use to record radius values
class ButtonClass4(object):
    """Implementation for Rcurve_tool_addin.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        global shpfile
        shpfile=pythonaddins.GetSelectedTOCLayerOrDataFrame()
        print(shpfile)
        
##step to the next feature in the shapefile        
#class ButtonClass5(object):
#    """Implementation for Rcurve_tool_addin.button_1 (Button)"""
#    def __init__(self):
#        self.enabled = True
#        self.checked = False
#    def onClick(self):
#        with arcpy.da.UpdateCursor(shpfile,['FID']) as cursor:
#            count=0
#            for row in cursor:
#                if count==0:
#                    arcpy.SelectLayerByAttribute_management(shpfile,"NEW_SELECTION",' "FID" = '+str(row[0]+1)+' ')
#                count=count+1
#                

class ToolClass7(object):
    """Implementation for Rcurve_tool_addin.tool (Tool)"""

    def __init__(self):
        self.enabled = True
        #create empty variables to hold coordinates and parameters of circles
        self.xcoords=[]
        self.ycoords=[]
        global centers        
        centers=[]
        global R        
        R=[]
        self.path=''
    def onMouseDownMap(self, x, y, button, shift):
        #on left click
        if button==1: 
            #if no map info has been set, set it on first click
            if self.path=='':
                global mxd
                mxd=arcpy.mapping.MapDocument('CURRENT') 
                self.path=os.path.dirname(mxd.filePath)
                #create shapefiles to hold point and circles so they can be visualized
                global pointsfile
                pointsfile=self.path+r'//tmp_points.shp'
                global circlefile
                circlefile=self.path+r'//tmp_circles.shp'
            #print the coordinate clicked and add it to the list of coordinates
            print(x,y)
            self.xcoords.append(x)
            self.ycoords.append(y)
            
            #create and visualize the point
            pt=arcpy.Point(x,y)
            arcpy.CopyFeatures_management(arcpy.PointGeometry(pt),pointsfile)
        
           

      
#    def onMouseUp(self, x, y, button, shift):
#        pass
#    def onMouseUpMap(self, x, y, button, shift):
#        pass
#    def onMouseMove(self, x, y, button, shift):
#        pass
#    def onMouseMoveMap(self, x, y, button, shift):
#        pass
    def onDblClick(self):

        #define corrdinates as arrays
        x=np.array(self.xcoords)
        y=np.array(self.ycoords)
        
        #create arrays used in circle calculation
        a1=np.array([x,y,np.ones(np.shape(x))])
        a2=np.array([-(x**2+y**2)])
        
        #solve the least squares fit to get the center point
        a=np.linalg.lstsq(a1.T,a2.T)[0]
        xc=-0.5*a[0]
        yc=-0.5*a[1]
        #record the center point   
        centers.append([xc,yc])
        
        #the circle radius is just the average distance from the center point
        Rtemp=np.mean(np.sqrt((x-xc)**2+(y-yc)**2))
        R.append(Rtemp) #record the radius
        
        
           
        #create a list of angles to be used when drawing the circle
        angles=np.array(list(range(0,360,4)))/360.*2*3.14159
        
        #create an empty list of circles
        circles=[]
        
        #step through all recorded circles
        for i in list(range(len(R))):
            #calculate points around the edge of each circle            
            circlepoints=[]
            for theta in angles:
                xtemp=float(R[i]*np.sin(theta)+centers[i][0])
                ytemp=float(R[i]*np.cos(theta)+centers[i][1])
             
                circlepoints.append([xtemp,ytemp])
                circles.append(arcpy.Polygon(arcpy.Array([arcpy.Point(*coords) for coords in circlepoints]))) #convert the points to a polygon and add it to the list
        arcpy.CopyFeatures_management(circles,circlefile) #add the list of polygons to the shapefile

        global Rmean
        Rmean=np.mean(R)

        #reset the coordinates
        self.xcoords=[]
        self.ycoords=[]
        print('Centers')
        print(centers)
        print('R')
        print(R)
        print('Rmean')
        print(Rmean)        
      
        arcpy.DeleteFeatures_management(arcpy.mapping.Layer(pointsfile))


#    def onKeyDown(self, keycode, shift):
#       pass

class ButtonClass6(object):
    """Implementation for Rcurve_tool_addin.button_1 (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        #record the average circle radius for the latest set of circles
        if np.isfinite(Rmean):
                #get the currently selected shapefile
            if shpfile: #If shapefile has been set, proceed
                #If there is no R_Curve field, add it
                if len(arcpy.ListFields(shpfile,'R_Curve'))==0:
                    arcpy.AddField_management(shpfile,'R_Curve','FLOAT')                
                    
                #access the attributes of the selected shapefile
                #count how many rows/features are currently selected
                with arcpy.da.UpdateCursor(shpfile,['FID','R_Curve']) as cursor:
                    count=0
                    for row in cursor:
                        count=count+1
                
                if count>1:  #if more than one feature is selected, give a warning
                    pythonaddins.MessageBox('Please select one feature in the shapefile!','Wrong number of features')
                if count==1: #if one feature is selected, record the average radius in the appropriate field
                    with arcpy.da.UpdateCursor(shpfile,['FID','R_Curve']) as cursor:
                        for row in cursor:
                            print('Setting R_Curve to: '+str(Rmean))
                            row[1]=Rmean
                            cursor.updateRow(row)
                            arcpy.SelectLayerByAttribute_management(shpfile,"NEW_SELECTION",' "FID" = '+str(row[0]+1)+' ') #re-select the row to refresh the table view
                            mxd.zoomToSelectedFeatures()
                    #reset global variables
                    global R
                    R=[]
                    global Rmean
                    Rmean=0
                    global centers
                    centers=[]
                    arcpy.DeleteFeatures_management(arcpy.mapping.Layer(circlefile))
                    
            else: #if nothing is selected, prompt the user
                pythonaddins.MessageBox('Please select a shapefile in the Table of Contents!','No shapefile selected')
#           
        else:
            pythonaddins.MessageBox('You need to measure a circle first!','No valid radius value')  
  
  
               