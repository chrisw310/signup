<%inherit file="base.mako"/>

<div class="row">
<div id="body" class="col-sm-12 col-md-8 col-md-offset-2">

<h1>2016 UQCS Registration</h1>
<div class="flash">
  % for category, msg in get_msgs(with_categories=True):
  <div class="alert alert-${category} alert-dismissible" role="alert">
    <button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>
    ${msg}
  </div>
  % endfor
</div>
<form method="POST" id='fullForm' action="../../" name="payForm">
  <div class="form-group">
    <label for="nameInput">Name <span class="reqstar">*</span></label>
    <input type="text" class="form-control" id="nameInput" placeholder="Name" name="name" required="true">
  </div>
  <div class="form-group">
    <label for="emailInput">Email address <span class="reqstar">*</span></label>
    <input name="email" type="email" class="form-control" id="emailInput" placeholder="Email" required="true">
  </div>
  <div class="form-group">
    <label>Gender</label>
    <div class="radio">
      <label>
        <input name="gender" type="radio" value="M">
        Male
      </label>
    </div>
    <div class="radio">
      <label>
        <input name="gender" type="radio" value="F">
        Female
      </label>
    </div>
    <div class="radio">
      <label>
        <input name="gender" type="radio" value="null" data-bind="checked: gender" checked>
        Prefer not to disclose
      </label>
    </div>
  </div>
  <div class="form-group">
    <label for="memberType">Member Type <span class="reqstar">*</span></label>
    <div class="checkbox">
        <label>
          <input name="student" type="checkbox" id="studentCheckbox">
          Are you currently a student?
        </label>
    </div>
  </div>
  <div id="student-form-section" style="display:none;">
    <div class="form-group">
      <label for="student-no">Student Number <span class="reqstar">*</span></label>
      <input type="number" name="student-no" class="form-control" id="studentNo" placeholder="43108765">
      <p class="help-block">8 digits, no 's'</p>
    </div>
    <div class="form-group">
      <label>Domestic or International</label>
      <div class="radio">
        <label>
          <input type="radio" value="domestic" name="domORint">
          Domestic
        </label>
      </div>
      <div class="radio">
        <label>
          <input type="radio" value="international" name="domORint">
          International
        </label>
      </div>
    </div>
    <div class="form-group">
      <label>Degree/Program</label>
      <input type="text" name='degree' class="form-control" placeholder="e.g. BEng (Software)">
    </div>
    <div class="form-group">
      <label>Degree Type</label>
      <div class="radio">
        <label>
          <input type="radio" value="undergrad" name="degreeType">
          Undergrad
        </label>
      </div>
      <div class="radio">
        <label>
          <input type="radio" value="postgrad" name="degreeType">
          Postgrad
        </label>
      </div>
    </div>
    <div class="form-group">
      <label>Year</label>
      <div class="form-control">
        <label class="radio-inline">
          <input type="radio" name="year" value="1"> 1
        </label>
        <label class="radio-inline">
          <input type="radio" name="year" value="2"> 2
        </label>
        <label class="radio-inline">
          <input type="radio" name="year" value="3"> 3
        </label>
        <label class="radio-inline">
          <input type="radio" name="year" value="4"> 4
        </label>
        <label class="radio-inline">
          <input type="radio" name="year" value="5+"> 5+
        </label>
      </div>
    </div>
  </div>
  <input type="hidden" name="stripeToken" value="" id='stripeToken'>
  <input class="btn btn-primary" name="submit" type="submit" id="payonline_submit" value="Pay Online">
  <input type="submit" name="submission" value="Pay Online" style="display:none;" id="submitbtn">
  <input class="btn btn-success" name="submission" type="submit" value="Pay Cash">
</form>
<div class="text-muted">
<p></p>
<p>Online payments have a 40c card surcharge.</p>
</div>
</div>
</div>
<script src="https://checkout.stripe.com/checkout.js"></script>
<script type="text/javascript">
var handler = StripeCheckout.configure({
  key: 'pk_live_Nsovfda3IOO0YXlDEOr1bOjb',
  locale: 'auto',
  token: function(token) {
    $('#stripeToken').val(token.id);
    $('#submitbtn').click();
  }
});
$('#payonline_submit').on('click', function(e){
  handler.open({
    name: 'UQCS',
    description: '2016 Membership',
    currency: "aud",
    amount: 540,
    'email': $('#emailInput').val()
  });
  e.preventDefault();
})
$(window).on('popstate', function() {
  handler.close();
});
$('#studentCheckbox').change(function(e){
  if($('#studentCheckbox')[0].checked){
    $('#student-form-section').slideDown();
    $('#studentNo').attr('required', 'true');
  } else {
    $('#student-form-section').slideUp();
    $('#studentNo').attr('required', null);
  }
});
</script>