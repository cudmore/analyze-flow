from aicsimageio import AICSImage

path = '/Users/cudmore/Dropbox/data/declan/Capillary6.oir'
img = AICSImage(path)

print('loaded:', path)

print('img.dims.order:', img.dims.order)  # TCZYX
print('img.shape:', img.shape)  # (30000, 1, 1, 1, 38)
# print(img)
print('img.dims.X:', img.dims.X)  # 38
print('img.dims.X:', img.dims.T)  # 
#print(img.dims.Y)  # 1

# none
# print('img.physical_pixel_sizes.X:', img.physical_pixel_sizes.X)
# print('img.physical_pixel_sizes.Y:', img.physical_pixel_sizes.X)

imgData = img.get_image_data('TX')
print('imgData:', imgData.shape)

# scenes?

print('current_scene:', img.current_scene) # Get the id of the current operating scene
print('scenes:', img.scenes)  # Get a list valid scene ids

# print('img.metadata:')
# print(img.metadata)

