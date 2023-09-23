#!/usr/bin/env python
# coding: utf-8

# ## Welcome to your notebook.
# 

# #### Run this cell to connect to your GIS and get started:

# In[1]:


from arcgis.gis import GIS
gis = GIS("home")


# #### Now you are ready to start!

# In[3]:


mymap = gis.map("Minnesota Road Map")


# In[4]:


mymap


# In[5]:


mnstreets = gis.content.get("7b79b33c2a0b4d81bb5ccb25e63006c9")


# In[6]:


mnstreets


# In[9]:


from arcgis import features


# In[10]:


features.use_proximity.create_buffers(input_layer=mnstreets, distances=[10], units='Feet', output_name='arcgis_online_buffers')


# In[ ]:




