<%inherit file="base.mako"/>
<div class="row">
<div>&nbsp;</div>
<div class="jumbotron">
<h1>Thank you for joining the UQ Computing Society!</h1>
% if member.has_paid():
<p>Your payment has been accepted and you are now a registered UQCS member!</p>
% else:
<p>Come visit our market day stall or our welcome event in order to pay for your year's membership</p>
% endif
</div>
</div>