<%inherit file="base.mako"/>

<div class="row">
<div id="body" class="col-md-12">
<h1> Listing of all members</h1>
<a href="#" class="btn btn-warning" onclick="window.location.reload()">Refresh</a>
<p>Registered: ${members.count()}</p>
<p>Paid: ${paid.count()}</p>
<table class="table table-bordered table-hover">
<thead>
<tr>
<td>Name</td>
<td>Email</td>
<td>Paid</td>
</tr>
</thead>
<tbody>
% for member in members:
<tr>
<td>${member.name}</td>
<td>${member.email}</td>
<td>${str(member.paid)}</td>
</tr>
%endfor
</tbody>
</table>
</div>
</div>