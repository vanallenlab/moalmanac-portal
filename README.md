**This service will be deprecated on 2026-01-05 due to [Google Cloud's deprecation of the Life Sciences API](https://support.terra.bio/hc/en-us/articles/38412190391579-June-27-2025). It may be revisited at a future date.**

***
# Molecular Oncology Almanac portal
The [Molecular Oncology Almanac portal](https://portal.moalmanac.org/) is a web portal built on top of [Google Cloud](https://cloud.google.com/) and the Broad Institute's [Terra](https://terra.bio/) which allows users to run the [Molecular Oncology Almanac](https://github.com/vanallenlab/moalmanac) on Terra, without needing to know GitHub, Python, or even Terra. Submitting molecular profiles through this portal will create a Terra workspace on the user's behalf, upload specified metadata and files, and run the Terra method [vanallenlab/moalmanac](https://portal.firecloud.org/?return=terra#methods/vanallenlab/moalmanac/). 

The Van Allen lab does **not** have access to any data or workspaces created through this portal. Only e-mail addresses are recorded in `users.db` for logged in and authentication purposes.

To run your own instance of this portal, view the [installation instructions](/docs/install.md).

## Using the portal
To use the Molecular Oncology Almanac portal, users must [have signed into Terra with a Google account](https://app.terra.bio/) and [be associated with a billing account on Terra](https://support.terra.bio/hc/en-us/articles/360026182251-How-to-set-up-billing-in-Terra). These requirements are visible from the [initial log in page](/img/login.png). Once satisfied, users can log in and are [presented with options](/img/logged_in.png) to either begin a new analysis, view previous analyses, and view workspaces on Terra. 

Users may log out by clicking their username in the top right corner and selecting `Logout` from the dropdown menu. 

### Beginning a new analysis
Selecting ["Begin new analysis"](/img/new_analyiss.png) redirects users to a form which allow them to specify several fields which are used to create a Terra workspace on the user's behalf. 

- `De-identified sample name`, a general name for the studied molecular profile. Only letters, numbers, underscores, and dashes are allowed.
- `Tumor type`, tumor ontology short and long codes from [Oncotree](http://oncotree.mskcc.org/#/home). Users can also enter their own.
- `Terra billing project`, a billing project to associate with the created workspace. 

Optional fields are available to allow users to either specify a workspace description and/or upload available data types for analysis. All fields have an information icon next to the header for more information and format.

All storage and compute costs associated with any runs will be billed to the specified billing project. 

### View previous analyses
Selecting ["View previous analyses"](/img/previous_analyses.png) redirects users to a list of workspaces tagged with `Molecular-Oncology-Almanac-Portal`, or the tag specified as `APP_TAG` in [`config.ini`](config.ini). This list is populated by making API requests on the users behalf so it may take a few seconds to load. The status of the submission is displayed and, when completed, will be replaced with a hyperlink to open the Molecular Oncology Almanac actionability report. A button also exists to open the underlying Terra workspace directly.

### View Terra workspaces
The third option presented to users is simply a hyperlink to view all workspaces tagged with `Molecular-Oncology-Almanac-Portal`, or the tag specified as `APP_TAG` in [`config.ini`](config.ini) on Terra.
