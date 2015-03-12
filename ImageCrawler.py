# -*- coding:utf-8 -*-

# Code for: Crawling image with tagging
# Date: 3/11

# 1. 특정 이미지 사이트에서 이미지를 크롤링하고
# 2. 이미지에 태그도 함께 가져온다. (태그없을시, 빈칸으로 두는데 (1)이미지 프로세싱으로 어느 정도 분위기를 판가름하여, 태그를 달아두는 방법 (2)사람들이 나중에 이미지와 함께 쓰는 문구(최다빈도)로 태그를 달아두는 기법이 있다. 두번이상이면 점수가 확 높아지도록)
#한 사람은 (이미지, 활), 한 사람은 (사진, 여자)면 이미지-사진이므로 이미지에 ++ 되어야할 것 같은데, 전혀다른놈으로 취급하는 것이 기분이 나쁜것이다.
# 3. 아마존 S3에 올리고, 반환된 URL까지 합쳐서
# access_key: AKIAJOH4Q6RE6S64Q5YQ
# secret_key: ^n28%|1snkNe
# bucket name: jeegle
# 4. MongoDB에도 아래의 스키마로 데이터를 밀어넣는다.
# {
# 	"title": "", # ===> X
# 	"source": {
# 			"name": "",
# 			"webpageUrl": ""
# 		},
# 	"originalImageUrl": "",
# 	"s3ImageUrl": "",
# 	"tag": ["", ""],
# 	"alt": "",  # ===> X
# 	"extra": {
#
# 	}
# }

# 1. 주의할 점은 최소한의 코드 변경으로 범용적으로 쓰일 크롤러를 만들어야 한다는 것이다.
# 2. 그리고 중간중간 막혔을때 기억하고 있어야 하는 일.. + 마지막 알아야

from bs4 import BeautifulSoup
import http.cookiejar
import urllib
import urllib.parse
import urllib.request
import re
import time
import sys
import json
import logging
from PIL import Image
from boto.s3.connection import S3Connection
import boto
import io

def ImageCralwer(name, url, start, end):
	for i in range(start, end):
		baseUrl = url + str(i)
		print("Get from: "+baseUrl)

		try:
			# Set user agent
			user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
			headers={'User-Agent':user_agent,} 
			request=urllib.request.Request(baseUrl,None,headers) #The assembled request

			# Crawl
			response = urllib.request.urlopen(request) # response http.client.HTTPResponse object
			data = response.read() # The data u need is html document

			# BeutifulSoup
			soup = BeautifulSoup(data)
			# print(soup.prettify())
			# Image URL
			ImageResult = soup.select('body > div.page-wrap > div > div > div > div > a')
			ImageUrl = ImageResult[0]['href']
			print(ImageResult[0]['href'])
			print(ImageResult[0].img['alt'])
			ImageFormat = ImageResult[0]['href'].split('.')
			ImageFormat = ImageFormat[-1]

			# Tags
			TagResult = soup.select('body > div.page-wrap > div > div > div.box.box--tags > ul')
			tags = []
			for tag in TagResult[0].find_all('strong'):
				tags.append(tag.get_text())

			# get Image
			request=urllib.request.Request(ImageUrl,None,headers) #The assembled request
			file_object = urllib.request.urlopen(request)
			img = io.BytesIO(file_object.read())
			# im = Image.open(img)
			# im.show()
			# im2 = im.resize((500, 500), Image.NEAREST)  
			# im2.show()

			# Amazon S3 connect and get image URL 
			conn = S3Connection('AKIAIETN6FONBPDPXYOA', 'cx3HzwLN9M8MxdQsfRpxsavJDeuyVBvjUYjNP6Pr')
			bucket = conn.get_bucket('jeegle')
			bucket.set_acl('public-read')

			k = bucket.new_key(str(i)+'.'+ImageFormat)
			k.set_metadata('Content-Type', 'image/jpeg')
			k.set_acl('public-read')
			# k.set_contents_from_stream(file_object.read()) #BotoClientError: s3 does not support chunked transfer
			# k.set_contents_from_stream(file_object) #BotoClientError: s3 does not support chunked transfer
			# k.set_contents_from_file(im)
			img.seek(0)
			k.set_contents_from_file(img)

			key_url = k.generate_url(expires_in=0, query_auth=False)
			print(key_url)

			# Call rest API
			headersJson={'User-Agent':user_agent,'Content-Type':'application/json'} 
			test_url = "http://sungpil.com/api/images"
			JsonData = json.dumps({'source': {'name':name, 'webpageUrl':baseUrl}, 'originalImageUrl':ImageUrl, 's3ImageUrl':key_url, 'tag':tags }).encode('utf-8')

			req = urllib.request.Request(test_url, JsonData, headersJson)
			response = urllib.request.urlopen(req)

			result =  response.read().decode("utf-8")
			print(result) 

		except Exception as e:
			print(e)

if __name__ == '__main__':
	ImageCralwer("pexels", "http://www.pexels.com/photo/", 1000, 5000)
