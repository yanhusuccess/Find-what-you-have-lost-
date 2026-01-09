from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, FileField, IntegerField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, NumberRange
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from difflib import SequenceMatcher
import os
import csv
from io import StringIO, BytesIO
from flask_admin import Admin, expose, AdminIndexView
from flask_admin.contrib.sqla import ModelView

# 初始化Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lostfound.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 确保上传文件夹存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 初始化数据库
db = SQLAlchemy(app)

# 初始化登录管理器
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录以访问此页面'

# 数据库模型
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    lost_items = db.relationship('LostItem', backref='author', lazy=True, foreign_keys='LostItem.user_id')
    found_items = db.relationship('FoundItem', backref='author', lazy=True, foreign_keys='FoundItem.user_id')
    comments = db.relationship('Comment', backref='author', lazy=True)
    messages_sent = db.relationship('Message', backref='sender', lazy=True, foreign_keys='Message.sender_id')
    messages_received = db.relationship('Message', backref='receiver', lazy=True, foreign_keys='Message.receiver_id')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class LostItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    lost_date = db.Column(db.DateTime, nullable=False)
    image = db.Column(db.String(200))
    status = db.Column(db.String(20), default='lost')  # lost, found, closed
    contact_info = db.Column(db.String(200))
    reward = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    views = db.Column(db.Integer, default=0)
    
    # 关系
    comments = db.relationship('Comment', backref='lost_item', lazy=True, foreign_keys='Comment.lost_item_id')
    
    def __repr__(self):
        return f'<LostItem {self.title}>'

class FoundItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    found_date = db.Column(db.DateTime, nullable=False)
    image = db.Column(db.String(200))
    status = db.Column(db.String(20), default='unclaimed')  # unclaimed, claimed, returned
    contact_info = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    views = db.Column(db.Integer, default=0)
    
    # 关系
    comments = db.relationship('Comment', backref='found_item', lazy=True, foreign_keys='Comment.found_item_id')
    
    def __repr__(self):
        return f'<FoundItem {self.title}>'

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lost_item_id = db.Column(db.Integer, db.ForeignKey('lost_item.id'))
    found_item_id = db.Column(db.Integer, db.ForeignKey('found_item.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Comment {self.id}>'

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Message {self.subject}>'

# 新增：收藏表
class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lost_item_id = db.Column(db.Integer, db.ForeignKey('lost_item.id'))
    found_item_id = db.Column(db.Integer, db.ForeignKey('found_item.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='favorites')
    lost_item = db.relationship('LostItem', backref='favorited_by')
    found_item = db.relationship('FoundItem', backref='favorited_by')
    
    def __repr__(self):
        return f'<Favorite {self.id}>'

# 新增：举报表
class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lost_item_id = db.Column(db.Integer, db.ForeignKey('lost_item.id'))
    found_item_id = db.Column(db.Integer, db.ForeignKey('found_item.id'))
    reason = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, reviewed, resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    reporter = db.relationship('User', backref='reports')
    lost_item = db.relationship('LostItem', backref='reports')
    found_item = db.relationship('FoundItem', backref='reports')
    
    def __repr__(self):
        return f'<Report {self.id}>'

# 新增：认领记录表
class ClaimRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    found_item_id = db.Column(db.Integer, db.ForeignKey('found_item.id'), nullable=False)
    claimer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    proof_description = db.Column(db.Text, nullable=False)
    proof_image = db.Column(db.String(200))
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    
    found_item = db.relationship('FoundItem', backref='claim_requests')
    claimer = db.relationship('User', backref='claim_requests')
    
    def __repr__(self):
        return f'<ClaimRequest {self.id}>'

# 新增：用户评分表
class UserRating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rater_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rated_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    rater = db.relationship('User', foreign_keys=[rater_id], backref='ratings_given')
    rated_user = db.relationship('User', foreign_keys=[rated_user_id], backref='ratings_received')
    
    def __repr__(self):
        return f'<UserRating {self.id}>'

# 表单类
class RegistrationForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    phone = StringField('手机号', validators=[Length(max=20)])
    password = PasswordField('密码', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('确认密码', validators=[DataRequired(), EqualTo('password')])
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('该用户名已被注册')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('该邮箱已被注册')

class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])

class LostItemForm(FlaskForm):
    title = StringField('物品名称', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('详细描述', validators=[DataRequired()])
    category = SelectField('物品类别', choices=[
        ('electronics', '电子产品'),
        ('documents', '证件文件'),
        ('accessories', '饰品配饰'),
        ('bags', '包袋'),
        ('keys', '钥匙'),
        ('pets', '宠物'),
        ('other', '其他')
    ], validators=[DataRequired()])
    location = StringField('丢失地点', validators=[DataRequired(), Length(max=200)])
    lost_date = StringField('丢失日期', validators=[DataRequired()])
    contact_info = StringField('联系方式', validators=[DataRequired(), Length(max=200)])
    reward = StringField('酬谢', validators=[Length(max=100)])
    image = FileField('上传图片')

class FoundItemForm(FlaskForm):
    title = StringField('物品名称', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('详细描述', validators=[DataRequired()])
    category = SelectField('物品类别', choices=[
        ('electronics', '电子产品'),
        ('documents', '证件文件'),
        ('accessories', '饰品配饰'),
        ('bags', '包袋'),
        ('keys', '钥匙'),
        ('pets', '宠物'),
        ('other', '其他')
    ], validators=[DataRequired()])
    location = StringField('拾取地点', validators=[DataRequired(), Length(max=200)])
    found_date = StringField('拾取日期', validators=[DataRequired()])
    contact_info = StringField('联系方式', validators=[DataRequired(), Length(max=200)])
    image = FileField('上传图片')

class CommentForm(FlaskForm):
    content = TextAreaField('评论内容', validators=[DataRequired(), Length(max=500)])

class MessageForm(FlaskForm):
    subject = StringField('主题', validators=[DataRequired(), Length(max=200)])
    content = TextAreaField('内容', validators=[DataRequired()])

# 新增：举报表单
class ReportForm(FlaskForm):
    reason = SelectField('举报原因', choices=[
        ('spam', '垃圾信息'),
        ('fraud', '虚假信息'),
        ('inappropriate', '不当内容'),
        ('duplicate', '重复发布'),
        ('other', '其他')
    ], validators=[DataRequired()])
    description = TextAreaField('详细说明', validators=[DataRequired(), Length(max=500)])

# 新增：认领表单
class ClaimForm(FlaskForm):
    proof_description = TextAreaField('证明描述', validators=[DataRequired(), Length(max=500)])
    proof_image = FileField('证明图片（可选）')

# 新增：评分表单
class RatingForm(FlaskForm):
    rating = SelectField('评分', choices=[
        ('5', '⭐⭐⭐⭐⭐ 非常好'),
        ('4', '⭐⭐⭐⭐ 好'),
        ('3', '⭐⭐⭐ 一般'),
        ('2', '⭐⭐ 较差'),
        ('1', '⭐ 很差')
    ], validators=[DataRequired()])
    comment = TextAreaField('评价内容（可选）', validators=[Length(max=200)])

# Flask-Admin 增强管理界面
class SecureModelView(ModelView):
    """安全的基础视图"""
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    
    def inaccessible_callback(self, name, **kwargs):
        flash('需要管理员权限才能访问', 'danger')
        return redirect(url_for('login'))

class UserAdminView(SecureModelView):
    """用户管理视图"""
    column_list = ['id', 'username', 'email', 'phone', 'is_admin', 'created_at']
    column_searchable_list = ['username', 'email', 'phone']
    column_filters = ['is_admin', 'created_at']
    column_sortable_list = ['id', 'username', 'email', 'created_at']
    column_labels = {
        'id': 'ID',
        'username': '用户名',
        'email': '邮箱',
        'phone': '手机号',
        'is_admin': '管理员',
        'created_at': '注册时间'
    }
    column_descriptions = {
        'username': '用户登录名',
        'is_admin': '是否为管理员权限'
    }
    form_excluded_columns = ['password_hash', 'lost_items', 'found_items', 'comments', 'messages_sent', 'messages_received']
    can_export = True
    export_types = ['csv', 'xlsx']
    
    def on_model_change(self, form, model, is_created):
        if is_created and hasattr(form, 'password'):
            model.set_password(form.password.data)

class LostItemAdminView(SecureModelView):
    """失物管理视图"""
    column_list = ['id', 'title', 'category', 'location', 'status', 'user_id', 'views', 'created_at']
    column_searchable_list = ['title', 'description', 'location']
    column_filters = ['category', 'status', 'created_at', 'lost_date']
    column_sortable_list = ['id', 'title', 'views', 'created_at']
    column_labels = {
        'id': 'ID',
        'title': '标题',
        'description': '描述',
        'category': '类别',
        'location': '地点',
        'lost_date': '丢失日期',
        'status': '状态',
        'contact_info': '联系方式',
        'reward': '酬谢',
        'user_id': '发布者ID',
        'views': '浏览量',
        'created_at': '发布时间'
    }
    column_formatters = {
        'category': lambda v, c, m, p: {
            'electronics': '电子产品',
            'documents': '证件文件',
            'accessories': '饰品配饰',
            'bags': '包袋',
            'keys': '钥匙',
            'pets': '宠物',
            'other': '其他'
        }.get(m.category, m.category),
        'status': lambda v, c, m, p: {
            'lost': '寻找中',
            'found': '已找到',
            'closed': '已关闭'
        }.get(m.status, m.status)
    }
    can_export = True
    export_types = ['csv', 'xlsx']

class FoundItemAdminView(SecureModelView):
    """拾物管理视图"""
    column_list = ['id', 'title', 'category', 'location', 'status', 'user_id', 'views', 'created_at']
    column_searchable_list = ['title', 'description', 'location']
    column_filters = ['category', 'status', 'created_at', 'found_date']
    column_sortable_list = ['id', 'title', 'views', 'created_at']
    column_labels = {
        'id': 'ID',
        'title': '标题',
        'description': '描述',
        'category': '类别',
        'location': '地点',
        'found_date': '拾取日期',
        'status': '状态',
        'contact_info': '联系方式',
        'user_id': '发布者ID',
        'views': '浏览量',
        'created_at': '发布时间'
    }
    column_formatters = {
        'category': lambda v, c, m, p: {
            'electronics': '电子产品',
            'documents': '证件文件',
            'accessories': '饰品配饰',
            'bags': '包袋',
            'keys': '钥匙',
            'pets': '宠物',
            'other': '其他'
        }.get(m.category, m.category),
        'status': lambda v, c, m, p: {
            'unclaimed': '待认领',
            'claimed': '已认领',
            'returned': '已归还'
        }.get(m.status, m.status)
    }
    can_export = True
    export_types = ['csv', 'xlsx']

class CommentAdminView(SecureModelView):
    """评论管理视图"""
    column_list = ['id', 'content', 'user_id', 'lost_item_id', 'found_item_id', 'created_at']
    column_searchable_list = ['content']
    column_filters = ['created_at', 'user_id']
    column_sortable_list = ['id', 'created_at']
    column_labels = {
        'id': 'ID',
        'content': '评论内容',
        'user_id': '评论者ID',
        'lost_item_id': '失物ID',
        'found_item_id': '拾物ID',
        'created_at': '评论时间'
    }
    can_export = True

class MessageAdminView(SecureModelView):
    """消息管理视图"""
    column_list = ['id', 'subject', 'sender_id', 'receiver_id', 'is_read', 'created_at']
    column_searchable_list = ['subject', 'content']
    column_filters = ['is_read', 'created_at']
    column_sortable_list = ['id', 'created_at']
    column_labels = {
        'id': 'ID',
        'subject': '主题',
        'content': '内容',
        'sender_id': '发送者ID',
        'receiver_id': '接收者ID',
        'is_read': '已读',
        'created_at': '发送时间'
    }
    can_export = True

class ReportAdminView(SecureModelView):
    """举报管理视图"""
    column_list = ['id', 'reason', 'status', 'reporter_id', 'lost_item_id', 'found_item_id', 'created_at']
    column_searchable_list = ['reason', 'description']
    column_filters = ['reason', 'status', 'created_at']
    column_sortable_list = ['id', 'created_at']
    column_labels = {
        'id': 'ID',
        'reporter_id': '举报者ID',
        'lost_item_id': '失物ID',
        'found_item_id': '拾物ID',
        'reason': '举报原因',
        'description': '详细说明',
        'status': '状态',
        'created_at': '举报时间'
    }
    column_formatters = {
        'reason': lambda v, c, m, p: {
            'spam': '垃圾信息',
            'fraud': '虚假信息',
            'inappropriate': '不当内容',
            'duplicate': '重复发布',
            'other': '其他'
        }.get(m.reason, m.reason),
        'status': lambda v, c, m, p: {
            'pending': '待处理',
            'reviewed': '已审核',
            'resolved': '已解决'
        }.get(m.status, m.status)
    }
    can_export = True

class ClaimRequestAdminView(SecureModelView):
    """认领管理视图"""
    column_list = ['id', 'found_item_id', 'claimer_id', 'status', 'created_at', 'reviewed_at']
    column_searchable_list = ['proof_description']
    column_filters = ['status', 'created_at']
    column_sortable_list = ['id', 'created_at']
    column_labels = {
        'id': 'ID',
        'found_item_id': '拾物ID',
        'claimer_id': '认领者ID',
        'proof_description': '证明描述',
        'proof_image': '证明图片',
        'status': '状态',
        'created_at': '申请时间',
        'reviewed_at': '审核时间'
    }
    column_formatters = {
        'status': lambda v, c, m, p: {
            'pending': '待审核',
            'approved': '已通过',
            'rejected': '已拒绝'
        }.get(m.status, m.status)
    }
    can_export = True

class UserRatingAdminView(SecureModelView):
    """评分管理视图"""
    column_list = ['id', 'rater_id', 'rated_user_id', 'rating', 'created_at']
    column_searchable_list = ['comment']
    column_filters = ['rating', 'created_at']
    column_sortable_list = ['id', 'rating', 'created_at']
    column_labels = {
        'id': 'ID',
        'rater_id': '评分者ID',
        'rated_user_id': '被评用户ID',
        'rating': '评分',
        'comment': '评价',
        'created_at': '评分时间'
    }
    can_export = True

class FavoriteAdminView(SecureModelView):
    """收藏管理视图"""
    column_list = ['id', 'user_id', 'lost_item_id', 'found_item_id', 'created_at']
    column_filters = ['created_at']
    column_sortable_list = ['id', 'created_at']
    column_labels = {
        'id': 'ID',
        'user_id': '用户ID',
        'lost_item_id': '失物ID',
        'found_item_id': '拾物ID',
        'created_at': '收藏时间'
    }
    can_export = True

# 自定义首页视图
class DashboardView(AdminIndexView):
    """管理后台首页视图"""
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    
    def inaccessible_callback(self, name, **kwargs):
        flash('需要管理员权限才能访问', 'danger')
        return redirect(url_for('login'))
    
    @expose('/')
    def index(self):
        # 统计数据
        total_users = User.query.count()
        total_lost = LostItem.query.count()
        total_found = FoundItem.query.count()
        total_comments = Comment.query.count()
        total_messages = Message.query.count()
        total_reports = Report.query.filter_by(status='pending').count()
        total_claims = ClaimRequest.query.filter_by(status='pending').count()
        
        # 最近活动
        recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
        recent_lost = LostItem.query.order_by(LostItem.created_at.desc()).limit(5).all()
        recent_found = FoundItem.query.order_by(FoundItem.created_at.desc()).limit(5).all()
        
        return self.render('admin/dashboard.html',
                         total_users=total_users,
                         total_lost=total_lost,
                         total_found=total_found,
                         total_comments=total_comments,
                         total_messages=total_messages,
                         total_reports=total_reports,
                         total_claims=total_claims,
                         recent_users=recent_users,
                         recent_lost=recent_lost,
                         recent_found=recent_found)

# 初始化Admin
admin = Admin(app, name='失物招领管理后台', template_mode='bootstrap4', index_view=DashboardView(name='控制台'))

# 添加视图
admin.add_view(UserAdminView(User, db.session, name='用户管理', category='用户'))
admin.add_view(UserRatingAdminView(UserRating, db.session, name='用户评分', category='用户'))

admin.add_view(LostItemAdminView(LostItem, db.session, name='失物管理', category='物品'))
admin.add_view(FoundItemAdminView(FoundItem, db.session, name='拾物管理', category='物品'))

admin.add_view(CommentAdminView(Comment, db.session, name='评论管理', category='互动'))
admin.add_view(MessageAdminView(Message, db.session, name='消息管理', category='互动'))
admin.add_view(FavoriteAdminView(Favorite, db.session, name='收藏管理', category='互动'))

admin.add_view(ReportAdminView(Report, db.session, name='举报管理', category='审核'))
admin.add_view(ClaimRequestAdminView(ClaimRequest, db.session, name='认领管理', category='审核'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 路由
@app.route('/')
def index():
    # 获取最新的失物和拾物信息
    recent_lost = LostItem.query.order_by(LostItem.created_at.desc()).limit(6).all()
    recent_found = FoundItem.query.order_by(FoundItem.created_at.desc()).limit(6).all()
    
    # 统计数据
    stats = {
        'total_lost': LostItem.query.count(),
        'total_found': FoundItem.query.count(),
        'total_users': User.query.count(),
        'success_cases': LostItem.query.filter_by(status='found').count() + FoundItem.query.filter_by(status='returned').count()
    }
    
    return render_template('index.html', recent_lost=recent_lost, recent_found=recent_found, stats=stats)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            phone=form.phone.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('注册成功！请登录', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('登录成功！', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('用户名或密码错误', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已退出登录', 'info')
    return redirect(url_for('index'))

@app.route('/lost')
def lost_list():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    
    query = LostItem.query
    
    if category:
        query = query.filter_by(category=category)
    
    if search:
        query = query.filter(
            db.or_(
                LostItem.title.contains(search),
                LostItem.description.contains(search),
                LostItem.location.contains(search)
            )
        )
    
    items = query.order_by(LostItem.created_at.desc()).paginate(page=page, per_page=12, error_out=False)
    
    return render_template('lost_list.html', items=items, category=category, search=search)

@app.route('/found')
def found_list():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    
    query = FoundItem.query
    
    if category:
        query = query.filter_by(category=category)
    
    if search:
        query = query.filter(
            db.or_(
                FoundItem.title.contains(search),
                FoundItem.description.contains(search),
                FoundItem.location.contains(search)
            )
        )
    
    items = query.order_by(FoundItem.created_at.desc()).paginate(page=page, per_page=12, error_out=False)
    
    return render_template('found_list.html', items=items, category=category, search=search)

@app.route('/lost/new', methods=['GET', 'POST'])
@login_required
def new_lost():
    form = LostItemForm()
    if form.validate_on_submit():
        filename = None
        if form.image.data:
            file = form.image.data
            filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        item = LostItem(
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            location=form.location.data,
            lost_date=datetime.strptime(form.lost_date.data, '%Y-%m-%d'),
            contact_info=form.contact_info.data,
            reward=form.reward.data,
            image=filename,
            user_id=current_user.id
        )
        db.session.add(item)
        db.session.commit()
        flash('失物信息发布成功！', 'success')
        return redirect(url_for('lost_detail', id=item.id))
    
    return render_template('new_lost.html', form=form)

@app.route('/found/new', methods=['GET', 'POST'])
@login_required
def new_found():
    form = FoundItemForm()
    if form.validate_on_submit():
        filename = None
        if form.image.data:
            file = form.image.data
            filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        item = FoundItem(
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            location=form.location.data,
            found_date=datetime.strptime(form.found_date.data, '%Y-%m-%d'),
            contact_info=form.contact_info.data,
            image=filename,
            user_id=current_user.id
        )
        db.session.add(item)
        db.session.commit()
        flash('拾物信息发布成功！', 'success')
        return redirect(url_for('found_detail', id=item.id))
    
    return render_template('new_found.html', form=form)

@app.route('/lost/<int:id>')
def lost_detail(id):
    item = LostItem.query.get_or_404(id)
    item.views += 1
    db.session.commit()
    
    comments = Comment.query.filter_by(lost_item_id=id).order_by(Comment.created_at.desc()).all()
    comment_form = CommentForm()
    
    # 检查当前用户是否已收藏
    is_favorited = False
    if current_user.is_authenticated:
        is_favorited = Favorite.query.filter_by(
            user_id=current_user.id, 
            lost_item_id=id
        ).first() is not None
    
    return render_template('lost_detail.html', item=item, comments=comments, 
                         comment_form=comment_form, is_favorited=is_favorited)

@app.route('/found/<int:id>')
def found_detail(id):
    item = FoundItem.query.get_or_404(id)
    item.views += 1
    db.session.commit()
    
    comments = Comment.query.filter_by(found_item_id=id).order_by(Comment.created_at.desc()).all()
    comment_form = CommentForm()
    
    # 检查当前用户是否已收藏
    is_favorited = False
    if current_user.is_authenticated:
        is_favorited = Favorite.query.filter_by(
            user_id=current_user.id, 
            found_item_id=id
        ).first() is not None
    
    return render_template('found_detail.html', item=item, comments=comments, 
                         comment_form=comment_form, is_favorited=is_favorited)

@app.route('/lost/<int:id>/comment', methods=['POST'])
@login_required
def comment_lost(id):
    item = LostItem.query.get_or_404(id)
    form = CommentForm()
    
    if form.validate_on_submit():
        comment = Comment(
            content=form.content.data,
            user_id=current_user.id,
            lost_item_id=id
        )
        db.session.add(comment)
        db.session.commit()
        flash('评论发布成功！', 'success')
    
    return redirect(url_for('lost_detail', id=id))

@app.route('/found/<int:id>/comment', methods=['POST'])
@login_required
def comment_found(id):
    item = FoundItem.query.get_or_404(id)
    form = CommentForm()
    
    if form.validate_on_submit():
        comment = Comment(
            content=form.content.data,
            user_id=current_user.id,
            found_item_id=id
        )
        db.session.add(comment)
        db.session.commit()
        flash('评论发布成功！', 'success')
    
    return redirect(url_for('found_detail', id=id))

@app.route('/profile')
@login_required
def profile():
    my_lost_items = LostItem.query.filter_by(user_id=current_user.id).order_by(LostItem.created_at.desc()).all()
    my_found_items = FoundItem.query.filter_by(user_id=current_user.id).order_by(FoundItem.created_at.desc()).all()
    
    return render_template('profile.html', my_lost_items=my_lost_items, my_found_items=my_found_items)

@app.route('/messages')
@login_required
def messages():
    received = Message.query.filter_by(receiver_id=current_user.id).order_by(Message.created_at.desc()).all()
    sent = Message.query.filter_by(sender_id=current_user.id).order_by(Message.created_at.desc()).all()
    
    return render_template('messages.html', received=received, sent=sent)

@app.route('/messages/send/<int:user_id>', methods=['GET', 'POST'])
@login_required
def send_message(user_id):
    receiver = User.query.get_or_404(user_id)
    form = MessageForm()
    
    if form.validate_on_submit():
        message = Message(
            subject=form.subject.data,
            content=form.content.data,
            sender_id=current_user.id,
            receiver_id=user_id
        )
        db.session.add(message)
        db.session.commit()
        flash('消息发送成功！', 'success')
        return redirect(url_for('messages'))
    
    return render_template('send_message.html', form=form, receiver=receiver)

@app.route('/messages/<int:id>/read')
@login_required
def read_message(id):
    message = Message.query.get_or_404(id)
    
    if message.receiver_id != current_user.id and message.sender_id != current_user.id:
        flash('无权访问此消息', 'danger')
        return redirect(url_for('messages'))
    
    if message.receiver_id == current_user.id and not message.is_read:
        message.is_read = True
        db.session.commit()
    
    return render_template('read_message.html', message=message)

@app.route('/lost/<int:id>/update_status/<status>')
@login_required
def update_lost_status(id, status):
    item = LostItem.query.get_or_404(id)
    
    if item.user_id != current_user.id and not current_user.is_admin:
        flash('无权修改此条目', 'danger')
        return redirect(url_for('lost_detail', id=id))
    
    if status in ['lost', 'found', 'closed']:
        item.status = status
        db.session.commit()
        flash('状态更新成功！', 'success')
    
    return redirect(url_for('lost_detail', id=id))

@app.route('/found/<int:id>/update_status/<status>')
@login_required
def update_found_status(id, status):
    item = FoundItem.query.get_or_404(id)
    
    if item.user_id != current_user.id and not current_user.is_admin:
        flash('无权修改此条目', 'danger')
        return redirect(url_for('found_detail', id=id))
    
    if status in ['unclaimed', 'claimed', 'returned']:
        item.status = status
        db.session.commit()
        flash('状态更新成功！', 'success')
    
    return redirect(url_for('found_detail', id=id))

@app.route('/statistics')
def statistics():
    # 各类别统计
    categories = ['electronics', 'documents', 'accessories', 'bags', 'keys', 'pets', 'other']
    category_labels = {
        'electronics': '电子产品',
        'documents': '证件文件',
        'accessories': '饰品配饰',
        'bags': '包袋',
        'keys': '钥匙',
        'pets': '宠物',
        'other': '其他'
    }
    
    lost_by_category = {}
    found_by_category = {}
    
    for cat in categories:
        lost_by_category[category_labels[cat]] = LostItem.query.filter_by(category=cat).count()
        found_by_category[category_labels[cat]] = FoundItem.query.filter_by(category=cat).count()
    
    # 状态统计
    lost_status = {
        '寻找中': LostItem.query.filter_by(status='lost').count(),
        '已找到': LostItem.query.filter_by(status='found').count(),
        '已关闭': LostItem.query.filter_by(status='closed').count()
    }
    
    found_status = {
        '待认领': FoundItem.query.filter_by(status='unclaimed').count(),
        '已认领': FoundItem.query.filter_by(status='claimed').count(),
        '已归还': FoundItem.query.filter_by(status='returned').count()
    }
    
    # 总体统计
    total_stats = {
        'total_items': LostItem.query.count() + FoundItem.query.count(),
        'total_users': User.query.count(),
        'total_comments': Comment.query.count(),
        'success_rate': round((LostItem.query.filter_by(status='found').count() + FoundItem.query.filter_by(status='returned').count()) / max(LostItem.query.count() + FoundItem.query.count(), 1) * 100, 1)
    }
    
    return render_template('statistics.html', 
                         lost_by_category=lost_by_category,
                         found_by_category=found_by_category,
                         lost_status=lost_status,
                         found_status=found_status,
                         total_stats=total_stats)

@app.route('/api/unread_messages')
@login_required
def unread_messages():
    count = Message.query.filter_by(receiver_id=current_user.id, is_read=False).count()
    return jsonify({'count': count})

# 新增：收藏功能
@app.route('/lost/<int:id>/favorite', methods=['POST'])
@login_required
def favorite_lost(id):
    item = LostItem.query.get_or_404(id)
    existing = Favorite.query.filter_by(user_id=current_user.id, lost_item_id=id).first()
    
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'favorited': False, 'message': '已取消收藏'})
    else:
        favorite = Favorite(user_id=current_user.id, lost_item_id=id)
        db.session.add(favorite)
        db.session.commit()
        return jsonify({'favorited': True, 'message': '收藏成功'})

@app.route('/found/<int:id>/favorite', methods=['POST'])
@login_required
def favorite_found(id):
    item = FoundItem.query.get_or_404(id)
    existing = Favorite.query.filter_by(user_id=current_user.id, found_item_id=id).first()
    
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'favorited': False, 'message': '已取消收藏'})
    else:
        favorite = Favorite(user_id=current_user.id, found_item_id=id)
        db.session.add(favorite)
        db.session.commit()
        return jsonify({'favorited': True, 'message': '收藏成功'})

@app.route('/favorites')
@login_required
def favorites():
    favorites = Favorite.query.filter_by(user_id=current_user.id).order_by(Favorite.created_at.desc()).all()
    return render_template('favorites.html', favorites=favorites)

# 新增：举报功能
@app.route('/lost/<int:id>/report', methods=['GET', 'POST'])
@login_required
def report_lost(id):
    item = LostItem.query.get_or_404(id)
    form = ReportForm()
    
    if form.validate_on_submit():
        report = Report(
            reporter_id=current_user.id,
            lost_item_id=id,
            reason=form.reason.data,
            description=form.description.data
        )
        db.session.add(report)
        db.session.commit()
        flash('举报已提交，我们会尽快处理', 'success')
        return redirect(url_for('lost_detail', id=id))
    
    return render_template('report.html', form=form, item=item, item_type='lost')

@app.route('/found/<int:id>/report', methods=['GET', 'POST'])
@login_required
def report_found(id):
    item = FoundItem.query.get_or_404(id)
    form = ReportForm()
    
    if form.validate_on_submit():
        report = Report(
            reporter_id=current_user.id,
            found_item_id=id,
            reason=form.reason.data,
            description=form.description.data
        )
        db.session.add(report)
        db.session.commit()
        flash('举报已提交，我们会尽快处理', 'success')
        return redirect(url_for('found_detail', id=id))
    
    return render_template('report.html', form=form, item=item, item_type='found')

# 新增：认领功能
@app.route('/found/<int:id>/claim', methods=['GET', 'POST'])
@login_required
def claim_item(id):
    item = FoundItem.query.get_or_404(id)
    
    # 检查是否已经提交过认领
    existing_claim = ClaimRequest.query.filter_by(
        found_item_id=id,
        claimer_id=current_user.id,
        status='pending'
    ).first()
    
    if existing_claim:
        flash('您已提交过认领申请，请耐心等待审核', 'warning')
        return redirect(url_for('found_detail', id=id))
    
    form = ClaimForm()
    
    if form.validate_on_submit():
        filename = None
        if form.proof_image.data:
            file = form.proof_image.data
            filename = secure_filename(f"claim_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        claim = ClaimRequest(
            found_item_id=id,
            claimer_id=current_user.id,
            proof_description=form.proof_description.data,
            proof_image=filename
        )
        db.session.add(claim)
        db.session.commit()
        
        # 通知发布者
        message = Message(
            subject=f'有人申请认领您发布的物品：{item.title}',
            content=f'用户 {current_user.username} 申请认领您发布的物品，请前往查看认领详情。',
            sender_id=current_user.id,
            receiver_id=item.user_id
        )
        db.session.add(message)
        db.session.commit()
        
        flash('认领申请已提交！', 'success')
        return redirect(url_for('my_claims'))
    
    return render_template('claim_item.html', form=form, item=item)

@app.route('/my-claims')
@login_required
def my_claims():
    # 我申请的认领
    my_claim_requests = ClaimRequest.query.filter_by(claimer_id=current_user.id).order_by(ClaimRequest.created_at.desc()).all()
    
    # 我发布物品的认领请求
    my_items_claims = ClaimRequest.query.join(FoundItem).filter(
        FoundItem.user_id == current_user.id
    ).order_by(ClaimRequest.created_at.desc()).all()
    
    return render_template('my_claims.html', my_claim_requests=my_claim_requests, my_items_claims=my_items_claims)

@app.route('/claim/<int:id>/review/<action>')
@login_required
def review_claim(id, action):
    claim = ClaimRequest.query.get_or_404(id)
    
    if claim.found_item.user_id != current_user.id:
        flash('无权操作此认领申请', 'danger')
        return redirect(url_for('my_claims'))
    
    if action == 'approve':
        claim.status = 'approved'
        claim.reviewed_at = datetime.utcnow()
        claim.found_item.status = 'returned'
        
        # 通知认领者
        message = Message(
            subject=f'您的认领申请已通过',
            content=f'您申请认领的物品"{claim.found_item.title}"已被批准，请联系发布者领取。',
            sender_id=current_user.id,
            receiver_id=claim.claimer_id
        )
        db.session.add(message)
        flash('已通过认领申请', 'success')
    elif action == 'reject':
        claim.status = 'rejected'
        claim.reviewed_at = datetime.utcnow()
        
        # 通知认领者
        message = Message(
            subject=f'您的认领申请未通过',
            content=f'很抱歉，您申请认领的物品"{claim.found_item.title}"未通过审核。',
            sender_id=current_user.id,
            receiver_id=claim.claimer_id
        )
        db.session.add(message)
        flash('已拒绝认领申请', 'info')
    
    db.session.commit()
    return redirect(url_for('my_claims'))

# 新增：用户评分功能
@app.route('/user/<int:user_id>/rate', methods=['GET', 'POST'])
@login_required
def rate_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user_id == current_user.id:
        flash('不能给自己评分', 'warning')
        return redirect(url_for('profile'))
    
    # 检查是否已评分
    existing = UserRating.query.filter_by(rater_id=current_user.id, rated_user_id=user_id).first()
    
    form = RatingForm()
    
    if form.validate_on_submit():
        if existing:
            existing.rating = int(form.rating.data)
            existing.comment = form.comment.data
            flash('评分已更新', 'success')
        else:
            rating = UserRating(
                rater_id=current_user.id,
                rated_user_id=user_id,
                rating=int(form.rating.data),
                comment=form.comment.data
            )
            db.session.add(rating)
            flash('评分成功', 'success')
        
        db.session.commit()
        return redirect(url_for('user_profile', user_id=user_id))
    
    if existing:
        form.rating.data = str(existing.rating)
        form.comment.data = existing.comment
    
    return render_template('rate_user.html', form=form, user=user)

@app.route('/user/<int:user_id>')
def user_profile(user_id):
    user = User.query.get_or_404(user_id)
    
    # 计算平均评分
    ratings = UserRating.query.filter_by(rated_user_id=user_id).all()
    avg_rating = sum(r.rating for r in ratings) / len(ratings) if ratings else 0
    
    # 用户发布的物品
    lost_items = LostItem.query.filter_by(user_id=user_id).order_by(LostItem.created_at.desc()).limit(5).all()
    found_items = FoundItem.query.filter_by(user_id=user_id).order_by(FoundItem.created_at.desc()).limit(5).all()
    
    return render_template('user_profile.html', user=user, avg_rating=avg_rating, 
                         ratings=ratings, lost_items=lost_items, found_items=found_items)

# 新增：智能匹配推荐
@app.route('/recommendations')
@login_required
def recommendations():
    # 获取我的失物
    my_lost_items = LostItem.query.filter_by(user_id=current_user.id, status='lost').all()
    recommendations = []
    
    for lost_item in my_lost_items:
        # 查找相似的拾物
        found_items = FoundItem.query.filter_by(category=lost_item.category, status='unclaimed').all()
        
        for found_item in found_items:
            # 计算相似度
            similarity = calculate_similarity(lost_item, found_item)
            if similarity > 0.3:  # 相似度阈值
                recommendations.append({
                    'lost_item': lost_item,
                    'found_item': found_item,
                    'similarity': round(similarity * 100, 1)
                })
    
    # 按相似度排序
    recommendations.sort(key=lambda x: x['similarity'], reverse=True)
    
    return render_template('recommendations.html', recommendations=recommendations)

def calculate_similarity(lost_item, found_item):
    """计算失物和拾物的相似度"""
    score = 0.0
    
    # 类别匹配（权重0.3）
    if lost_item.category == found_item.category:
        score += 0.3
    
    # 标题相似度（权重0.3）
    title_sim = SequenceMatcher(None, lost_item.title.lower(), found_item.title.lower()).ratio()
    score += title_sim * 0.3
    
    # 描述相似度（权重0.2）
    desc_sim = SequenceMatcher(None, lost_item.description.lower(), found_item.description.lower()).ratio()
    score += desc_sim * 0.2
    
    # 地点相似度（权重0.2）
    if lost_item.location.lower() in found_item.location.lower() or found_item.location.lower() in lost_item.location.lower():
        score += 0.2
    
    return score

# 新增：高级搜索
@app.route('/advanced-search')
def advanced_search():
    item_type = request.args.get('type', 'lost')  # lost or found
    category = request.args.get('category', '')
    keyword = request.args.get('keyword', '')
    location = request.args.get('location', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    status = request.args.get('status', '')
    sort = request.args.get('sort', 'newest')  # newest, oldest, most_viewed
    
    if item_type == 'lost':
        query = LostItem.query
        if category:
            query = query.filter_by(category=category)
        if keyword:
            query = query.filter(
                db.or_(
                    LostItem.title.contains(keyword),
                    LostItem.description.contains(keyword)
                )
            )
        if location:
            query = query.filter(LostItem.location.contains(location))
        if date_from:
            query = query.filter(LostItem.lost_date >= datetime.strptime(date_from, '%Y-%m-%d'))
        if date_to:
            query = query.filter(LostItem.lost_date <= datetime.strptime(date_to, '%Y-%m-%d'))
        if status:
            query = query.filter_by(status=status)
        
        # 排序
        if sort == 'oldest':
            query = query.order_by(LostItem.created_at.asc())
        elif sort == 'most_viewed':
            query = query.order_by(LostItem.views.desc())
        else:  # newest
            query = query.order_by(LostItem.created_at.desc())
        
        items = query.all()
    else:
        query = FoundItem.query
        if category:
            query = query.filter_by(category=category)
        if keyword:
            query = query.filter(
                db.or_(
                    FoundItem.title.contains(keyword),
                    FoundItem.description.contains(keyword)
                )
            )
        if location:
            query = query.filter(FoundItem.location.contains(location))
        if date_from:
            query = query.filter(FoundItem.found_date >= datetime.strptime(date_from, '%Y-%m-%d'))
        if date_to:
            query = query.filter(FoundItem.found_date <= datetime.strptime(date_to, '%Y-%m-%d'))
        if status:
            query = query.filter_by(status=status)
        
        # 排序
        if sort == 'oldest':
            query = query.order_by(FoundItem.created_at.asc())
        elif sort == 'most_viewed':
            query = query.order_by(FoundItem.views.desc())
        else:  # newest
            query = query.order_by(FoundItem.created_at.desc())
        
        items = query.all()
    
    return render_template('advanced_search.html', items=items, item_type=item_type,
                         category=category, keyword=keyword, location=location,
                         date_from=date_from, date_to=date_to, status=status, sort=sort)

# 新增：数据导出
@app.route('/export/lost')
@login_required
def export_lost():
    items = LostItem.query.filter_by(user_id=current_user.id).all()
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', '标题', '类别', '描述', '丢失地点', '丢失日期', '状态', '联系方式', '酬谢', '浏览次数', '发布时间'])
    
    for item in items:
        writer.writerow([
            item.id,
            item.title,
            item.category,
            item.description,
            item.location,
            item.lost_date.strftime('%Y-%m-%d'),
            item.status,
            item.contact_info,
            item.reward or '',
            item.views,
            item.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    output.seek(0)
    return send_file(
        BytesIO(output.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'my_lost_items_{datetime.now().strftime("%Y%m%d")}.csv'
    )

@app.route('/export/found')
@login_required
def export_found():
    items = FoundItem.query.filter_by(user_id=current_user.id).all()
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', '标题', '类别', '描述', '拾取地点', '拾取日期', '状态', '联系方式', '浏览次数', '发布时间'])
    
    for item in items:
        writer.writerow([
            item.id,
            item.title,
            item.category,
            item.description,
            item.location,
            item.found_date.strftime('%Y-%m-%d'),
            item.status,
            item.contact_info,
            item.views,
            item.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    output.seek(0)
    return send_file(
        BytesIO(output.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'my_found_items_{datetime.now().strftime("%Y%m%d")}.csv'
    )

# 错误处理
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # 创建管理员账号（如果不存在）
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@lostfound.com',
                is_admin=True
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            print('管理员账号创建成功：username=admin, password=admin123')
    
    print('=' * 60)
    print('失物招领系统启动成功！')
    print('=' * 60)
    print('请使用以下任一地址访问:')
    print('  本地访问: http://127.0.0.1:5000')
    print('  本地访问: http://localhost:5000')
    print('  管理后台: http://localhost:5000/admin')
    print('  默认账号: admin / admin123')
    print('=' * 60)
    
    app.run(debug=True, host='127.0.0.1', port=5000)

