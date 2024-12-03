from flask import Flask, render_template, request ,jsonify
from app import app
import requests
import os
import json
from app import app
from io import BytesIO


@app.route('/detect_fraud_profile', methods=['POST'])
def detect_fraud_profile():
    # Parse JSON from request
    data = request.get_json()
    print(data)
    username = data.get('username') # Extract 'username' from the JSON payload
    print(username)
 
    if not username:
        return jsonify({'error': 'Username is required.'}), 400

    # Call your function with the username
    user_information_final(username)

    return jsonify({'result': f"Data for '{username}' has been successfully processed."})


# fetch the user information
def get_user_data(username):
    url = "https://instagram-scraper-api2.p.rapidapi.com/v1/info"
    querystring = {"username_or_id_or_url": username}
    headers = {
        'x-rapidapi-key': "618161e39amshf02b15c33178cc2p172012jsna5184d434c4e",
        'x-rapidapi-host': "instagram-scraper-api2.p.rapidapi.com"
    }
    # fetching the data from the api
    response = requests.get(url, headers=headers, params= querystring)
    if response.status_code == 200:
        return response.json()
    return None


# save the image to the device
def save_profile_picture(url, username):
    img_data = requests.get(url).content

    base_dir = os.path.join(os.getcwd(), username)
    os.makedirs(base_dir, exist_ok=True)

    profile_dir = os.path.join(base_dir, f"{username}_profile")
    os.makedirs(profile_dir, exist_ok=True)

    img_filename = 'profile_pic.jpg'

    img_path = os.path.join(base_dir,profile_dir, img_filename) 
    os.makedirs(os.path.dirname(img_path), exist_ok=True)

    with open(img_path,'wb') as file:
        file.write(img_data)
     

    return img_path


# Function to download the image and save it locally
def save_post_picture(img_url, username, post_index):
    # Get the image content


    base_dir = os.path.join(os.getcwd(), username)
    os.makedirs(base_dir, exist_ok=True)
    post_dir = os.path.join(base_dir, f"{username}_posts")
    os.makedirs(post_dir, exist_ok=True)

    img_data = requests.get(img_url).content
    img_filename = f'{username}_post_{post_index + 1}.jpg'
    img_path = os.path.join(base_dir,post_dir , img_filename)
    os.makedirs(os.path.dirname(img_path), exist_ok=True)  
    with open(img_path, 'wb') as file:
        file.write(img_data)
        
    # Return the relative path for use in the template
    return img_path

# Function to fetch recent posts using Instagram scraper API
def get_recent_posts(username):
    url = "https://instagram-scraper-api2.p.rapidapi.com/v1.2/posts"
    querystring = {"username_or_id_or_url": username}
    headers = {
	"x-rapidapi-key": "618161e39amshf02b15c33178cc2p172012jsna5184d434c4e",
	"x-rapidapi-host": "instagram-scraper-api2.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring)
    data = response.json()
    posts = []
    
    if 'data' in data and 'items' in data['data']:
        posts = data['data']['items'][:10]  # Only take the first 5 posts

        # Extract only required caption information
        for post_index, post in enumerate(posts):
            caption_info = post.get('caption', {})
            post['caption_text'] = caption_info.get('text', 'No caption text available')
            post['did_report_as_spam'] = caption_info.get('did_report_as_spam', "False")
            post['created_at'] = caption_info.get('created_at', 'Unknown time')
            del post['caption']  # Optionally remove the full caption data

            image_versions = post.get('image_versions', {}).get('items', [])
            if image_versions:
                # Select the highest resolution image URL (based on the largest 'height' or 'width')
                best_image = min(image_versions, key=lambda x: x['height'] if 'height' in x else x['width'])
                post['image_url'] = best_image['url']
            else:
                post['image_url'] = None
            img_url = post['image_url']
            if img_url:
                post['image_path'] = save_post_picture(img_url, username, post_index)
        
    return posts



def profile_pic(username):
    user_data = get_user_data(username)
    profile_pic_url = user_data['data']['profile_pic_url']
    username = user_data['data']['username']
    profile_pic_path = save_profile_picture(profile_pic_url, username)
    return profile_pic_path



def user_information_final(username):
    user_data = get_user_data(username)
    print(user_data)

    base_dir = os.path.join(os.getcwd(), username)
    os.makedirs(base_dir, exist_ok=True)
    # caption
    caption_dir = os.path.join(base_dir, f"{username}_captions")
    os.makedirs(caption_dir, exist_ok=True)
    # profile
    profile_dir = os.path.join(base_dir, f"{username}_profile")
    os.makedirs(profile_dir, exist_ok=True)

    if not user_data:
        return {"error": f"Unable to fetch the data for the username: {username}"}
    # Extract basic user information
    data = user_data.get('data', {})
    user_info = {
        "Username": data.get("username", "N/A"),
        "Name": data.get("full_name", "N/A"),
        "Bio": data.get("biography", "N/A"),
        "Followers": data.get("follower_count", 0),
        "Following": data.get("following_count", 0),
        "NumberOfPosts": data.get("media_count", 0),
        "Verified": "Yes" if data.get("is_verified") else "No",
        "Account Privacy": "Private" if data.get("is_private") else "Public",
        "Profile Picture Path": profile_pic(username),
        "Posts": []
    }

    posts = get_recent_posts(username)
    captions = []


    profile_info_path = os.path.join(profile_dir, "profile_data.json")
    with open(profile_info_path, "w") as profile_info_file:
        json.dump(user_info, profile_info_file, indent=4)

    for index, post in enumerate(posts, start=1):
        post_info = {
            "PostNumber": index,
            "Caption": post.get("caption_text", "No caption text available") or "No captions available" ,
            "Upload Time": post.get("created_at", "Unknown time"),
        }
        captions.append(post_info)

    # save captions to captions.json
    captions_path = os.path.join(caption_dir,"captions.json")
    with open(captions_path,"w") as captions_file:
        json.dump(captions, captions_file, indent=4)

    return user_info




# @app.route("/instagram", methods=["GET","POST"])
# def index():
#     if request.method == "POST":
#         username = request.form["username"]

#         # fetch user data
#         user_data = get_user_data(username)
        
#         if user_data:
#             profile_pic_url = user_data['data']['profile_pic_url']
#             username = user_data['data']['username']
#             # save the profile pic locally
#             profile_pic_path = save_profile_picture(profile_pic_url, username)
#             # fetch the recent posts
#             posts  = get_recent_posts(username)
#             return render_template("index.html",data=user_data, profile_pic =  profile_pic_path , posts = posts)
#         else:
#             return f"Error:unable to fetch the data for the {username}",400
        
#     return render_template("index.html", data=None,profile_pic= None, posts = None )
        
if __name__ == "__main__":
    app.run(debug=True)

