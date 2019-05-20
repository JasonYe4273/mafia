import base64

def request_handler(request):
    address = '__HOME__/mafia/images/' + request['values']['image']
    image = open(address, 'rb') #open image using absolute path (__HOME__ keyword)
    b64_encoded= base64.encodestring(image.read()) #read image and encode it into base64
    #return simple html page with image in it that is packaged in using its base64 encoding:
    return """
<!DOCTYPE html>
<html>
<head>
  <title>Practice Title</title>
</head>
<body>
  <img src="data:image/jpg;base64, {}" alt="Red dot" />
</body>
</html>
    """.format(b64_encoded.decode("utf-8") ) #need that decode so the string we return is treated as string not bytestring
