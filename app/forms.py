from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import TextField, TextAreaField, validators, SelectField, StringField, SubmitField


class UploadForm(FlaskForm):
    billingProject = SelectField(u'FireCloud Billing Project:',
                                 default=1, validators=[validators.required()])
    patientId = TextField('De-identified patient id:',
                          validators=[validators.required()],
                          render_kw={'placeholder': 'de-identified-sample-name'})
    tumorType = TextField('Tumor Type:', validators=[validators.required()], render_kw={'placeholder': 'Glioblastoma'})
    snvHandle = FileField('Single Nucleotide Variants:', validators=[validators.optional()], default='')
    indelHandle = FileField('Insertions & Deletions:', validators=[validators.optional()], default='')
    segHandle = FileField('Copy Number Alterations:', validators=[validators.optional()], default='')
    fusionHandle = FileField('Fusions (from STAR Fusion):', validators=[validators.optional()], default='')
    burdenHandle = FileField('Somatic Covered Bases', validators=[validators.optional()], default='')
    germlineHandle = FileField('Germline Variants', validators=[validators.optional()], default='')
    dnarnaHandle = FileField('Single Nucleotide Variants (from RNA)', validators=[validators.optional()], default='')
    description = TextAreaField('Description:', validators=[validators.optional()])
    submit = SubmitField(label="Launch Analysis!")
