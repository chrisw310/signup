<%inherit file="base.mako"/>

<div class="row">
<div id="body" class="col-md-12">
<h1> Listing of unpaid members</h1>
<a href="#" class="btn btn-warning" onclick="window.location.reload()">Refresh</a>
<table class="table table-bordered table-hover">
<thead>
<tr>
<td>Name</td>
<td>Email</td>
<td></td>
</tr>
</thead>
<tbody>
% for member in members:
<tr>
<td>${member.name}</td>
<td>${member.email}</td>
<td><a href="/admin/paid/${member.id}" class="btn btn-default">Paid</a></td>
<td><a href="/admin/delete/${member.id}" class="btn btn-default">Paid</a></td>
</tr>
%endfor
</tbody>
</table>
</div>
</div>