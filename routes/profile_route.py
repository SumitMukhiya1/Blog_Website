from flask import render_template, request, redirect, url_for,flash
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
import os
import time
from routes.models_routes import db, Link, Skill, Post


def edit_profile(app):
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

    @app.route('/editing_profile', methods=['GET', 'POST'])
    def editing_profile_page():
        if request.method == 'POST':
            updated = False
            if 'profile_picture' in request.files:
                file = request.files['profile_picture']
                if file and file.filename != '':
                    if allowed_file(file.filename):
                        try:
                            # Generate unique filename to avoid conflicts
                            file_text = os.path.splitext(file.filename)[1]
                            filename = secure_filename(f"{current_user.id}_{int(time.time())}{file_text}")
                            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                            # Save file
                            file.save(file_path)
                            # Update database
                            current_user.profile_image = filename
                            flash('Profile picture updated successfully!', 'success')
                            updated = True
                        except Exception as e:
                            print(f"Error saving file: {str(e)}")
                            flash('Error updating profile picture', 'error')
                    else:
                        flash('Invalid file type', 'error')

            # getting other info from user

            # Handle skills FIRST (before any redirects)
            skills = request.form.getlist('skills')
            print("=== SKILLS DEBUG ===")
            print("Skills received:", skills)
            print("Number of skills:", len(skills))

            # Clear existing skills and add new ones
            skills_updated = False
            if skills:
                # First, clear all existing skills for this user
                Skill.query.filter_by(user_id=current_user.id).delete()

                # Add new skills
                for skill in skills:
                    if skill and skill.strip():  # Check if skill is not empty
                        print(f"Adding skill: '{skill}'")
                        new_skill = Skill(user_id=current_user.id, skill=skill.strip())
                        db.session.add(new_skill)
                        skills_updated = True

                if skills_updated:
                    flash('Skills updated successfully!', 'success')
                    updated = True

            username = request.form.get('user_name')
            if username and current_user.user_name != username:
                current_user.user_name = username
                flash('Username updated successfully!', 'success')
                updated = True

            about = request.form.get('about')
            if about and current_user.about != about:
                current_user.about = about
                flash('Your about updated successfully!', 'success')
                updated = True

            profession = request.form.get('profession')
            if profession and current_user.profession != profession:
                current_user.profession = profession
                flash('Your profession updated successfully!', 'success')
                updated = True

            bio = request.form.get('bio')
            if bio and current_user.bio != bio:
                current_user.bio = bio
                flash('Your bio updated successfully!', 'success')
                updated = True

            education = request.form.get('education')
            if education and current_user.education != education:
                current_user.education = education
                flash('Your education updated successfully!', 'success')
                updated = True

            country = request.form.get('country')
            if country and current_user.country != country:
                current_user.country = country
                flash('Your location updated successfully!', 'success')
                updated = True

            city = request.form.get('city')
            if city and current_user.city != city:
                current_user.city = city
                flash('Your location updated successfully!', 'success')
                updated = True

            # Handle links
            websites = request.form.getlist('website')
            links = request.form.getlist('link')

            print(f"DEBUG - All form data: {dict(request.form)}")
            print(f"DEBUG - Websites list: {websites}")
            print(f"DEBUG - Links list: {links}")
            print(f"DEBUG - Number of websites: {len(websites)}")
            print(f"DEBUG - Number of links: {len(links)}")

            # Clear existing links first
            Link.query.filter_by(user_id=current_user.id).delete()

            # Add new links
            links_added = False
            for i, (website, link_url) in enumerate(zip(websites, links)):
                print(f"DEBUG - Processing link {i}: website='{website}', link='{link_url}'")

                # Clean the data
                website = website.strip() if website else ''
                link_url = link_url.strip() if link_url else ''

                # Only add if both fields have values
                if website and link_url:
                    try:
                        new_link = Link(user_id=current_user.id, website=website, link=link_url)
                        db.session.add(new_link)
                        links_added = True
                        print(f'DEBUG - Link added: {website} - {link_url}')
                    except Exception as e:
                        print(f"Error adding link: {e}")
                else:
                    print(f"DEBUG - Skipping empty link: website='{website}', link='{link_url}'")

            if links_added:
                flash('Social links updated successfully!', 'success')
                print("DEBUG - Links committed to database")
                updated = True
            else:
                print("DEBUG - No valid links provided")

            # COMMIT ALL CHANGES AT ONCE
            if updated:
                db.session.commit()
                return redirect(url_for('editing_profile_page'))
            else:
                flash("No changes were made.", "info")
                return redirect(url_for('editing_profile_page'))

        # GET request - show the form
        user_links = Link.query.filter_by(user_id=current_user.id).all()
        user_skills = Skill.query.filter_by(user_id=current_user.id).all()

        print(user_links)
        user_info = {
            "fullname": current_user.fullname,
            "email": current_user.email,
            "profile_image": current_user.profile_image,
            "user_name": current_user.user_name,
            "about": current_user.about,
            "profession": current_user.profession,
            "bio": current_user.bio,
            "education": current_user.education,
            "country": current_user.country,
            "city": current_user.city,
            "links": user_links,
            "skills": [skill.skill for skill in user_skills],  # Convert to list of skill strings
        }

        return render_template('edite_profile.html', user_info=user_info)


    #user profile
    @app.route('/profile')
    @login_required
    def user_profile():
        user_links = Link.query.filter_by(user_id=current_user.id).all()
        user_skills = Skill.query.filter_by(user_id=current_user.id).all()
        user_all_blogs = Post.query.filter_by(user_id=current_user.id).all()

        user_info = {
            "fullname": current_user.fullname,
            "email": current_user.email,
            "profile_image": current_user.profile_image,
            "user_name": current_user.user_name,
            "about": current_user.about,
            "profession": current_user.profession,
            "bio": current_user.bio,
            "education": current_user.education,
            "location": f"{current_user.country} || {current_user.city}",
            "joined": current_user.joined,
            "links": user_links,
            "skills": [skill.skill for skill in user_skills],
            "user_all_blogs": str(len(user_all_blogs)),
            "user_posts": user_all_blogs
        }

        return render_template('profile.html', user_info=user_info)
