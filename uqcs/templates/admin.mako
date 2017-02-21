<%inherit file="base.mako"/>

<div class="row">
<div id="body" class="col-sm-12 col-md-8 col-md-offset-2">
<div class="flash">
    % for category, msg in get_msgs(with_categories=True):
        <div class="alert alert-${category} alert-dismissible" role="alert">
            <button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>
            ${msg}
        </div>
    % endfor
</div>
<form method="POST">
    <div class="form-group">
        <label for="username">Username<span class="reqstar">*</span></label>
        <input type="text" class="form-control" name="username" placeholder="Username" required="true">
    </div>
    <div class="form-group">
        <label for="password">Password<span class="reqstar">*</span></label>
        <input type="password" class="form-control" name="password" placeholder="Password" required="true">
    </div>
    <input class="btn btn-primary" name="submit" type="submit" value="Submit">
</form>
</div>
</div>