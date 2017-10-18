from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import TextField, TextAreaField, SelectField, validators, StringField, SubmitField

class UploadForm(FlaskForm):
    billingProject = SelectField(u'FireCloud Billing Project:',
                                 choices=[('1', 'Option 1'), ('2', 'Option 2')], default=1)
    patientId = TextField('Patient ID:', validators=[validators.required()])
    tumorType = TextField('Tumor Type:', validators=[validators.required()])
    snvHandle = FileField('Single Nucleotide Variants:', validators=[validators.optional()])
    indelHandle = FileField('Insertions & Deletions:', validators=[validators.optional()])
    segHandle = FileField('Copy Number Alterations:', validators=[validators.optional()])
    fusionHandle = FileField('Fusions (from STAR Fusion):', validators=[validators.optional()])
    burdenHandle = FileField('Somatic Covered Bases', validators=[validators.optional()])
    germlineHandle = FileField('Germline Variants', validators=[validators.optional()])
    dnarnaHandle = FileField('Single Nucleotide Variants (from RNA)', validators=[validators.optional()])
    description = TextAreaField('Description:', validators=[validators.optional()])
    submit = SubmitField(label="Launch Analysis!")