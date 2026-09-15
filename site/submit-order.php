<?php
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    header('Location: order.html');
    exit;
}

$to = 'elazarwhodoesthings@gmail.com';
$subject = 'Wonder Cabinet Order Inquiry';

// Sanitize inputs
$name     = htmlspecialchars(strip_tags($_POST['name'] ?? ''));
$email    = filter_var($_POST['email'] ?? '', FILTER_SANITIZE_EMAIL);
$phone    = htmlspecialchars(strip_tags($_POST['phone'] ?? ''));
$finish   = htmlspecialchars(strip_tags($_POST['finish'] ?? ''));
$sheen    = htmlspecialchars(strip_tags($_POST['sheen'] ?? ''));
$pi       = htmlspecialchars(strip_tags($_POST['pi_model'] ?? ''));
$joystick = htmlspecialchars(strip_tags($_POST['joystick_color'] ?? ''));
$buttons  = htmlspecialchars(strip_tags($_POST['button_color'] ?? ''));
$notes    = htmlspecialchars(strip_tags($_POST['notes'] ?? ''));

$body  = "New Wonder Cabinet order inquiry:\n\n";
$body .= "Name:            $name\n";
$body .= "Email:           $email\n";
$body .= "Phone:           $phone\n";
$body .= "Cabinet Finish:  $finish\n";
$body .= "Sheen:           $sheen\n";
$body .= "Raspberry Pi:    $pi\n";
$body .= "Joystick Color:  $joystick\n";
$body .= "Button Color:    $buttons\n";
$body .= "Notes:           $notes\n";

$headers  = "From: noreply@thiselazar.com\r\n";
$headers .= "Reply-To: $email\r\n";

$sent = mail($to, $subject, $body, $headers);
?>
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Wonder Cabinet - Order <?php echo $sent ? 'Received' : 'Error'; ?></title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=IBM+Plex+Mono:wght@400;500&display=swap">
<link rel="stylesheet" href="v2.css">
<style>
.result { max-width: 560px; margin: 0 auto; padding: 56px var(--gutter) 80px; text-align: center; }
.result h2 { font-size: 32px; font-weight: 500; margin-bottom: 14px; }
.result p { font-size: 19px; color: var(--ink-2); }
.result p + p { margin-top: 12px; }
</style>
</head>
<body>
<header class="masthead">
  <div class="wrap">
    <a class="brand" href="index.html">Wonder Cabinet</a>
    <nav class="nav" aria-label="Site">
      <a href="emulator.html">Emulator</a>
      <a href="guide.html">Field Guide</a>
      <a href="history.html">History</a>
      <a href="order.html">Order</a>
    </nav>
    <span class="status">MADE TO ORDER · FROM $495</span>
  </div>
</header>
<?php if ($sent): ?>
<div class="result">
  <h2>Inquiry Received</h2>
  <p>Thanks, <?php echo $name; ?>. We'll get back to you within 2 business days.</p>
  <p><a href="index.html">&larr; Back to home</a></p>
</div>
<?php else: ?>
<div class="result">
  <h2>Something Went Wrong</h2>
  <p>Your inquiry couldn't be sent. Please email us directly at
  <a href="mailto:elazarwhodoesthings@gmail.com">elazarwhodoesthings@gmail.com</a>.</p>
  <p><a href="order.html">&larr; Try again</a></p>
</div>
<?php endif; ?>
<footer>
  <div class="wrap">
    <span>Programmed with AI, designed &amp; curated by hand</span>
    <span><a href="https://github.com/thisElazar/ledarcade">Source</a> · <a href="https://thiselazar.com/">thiselazar.com</a></span>
  </div>
</footer>
</body>
</html>
