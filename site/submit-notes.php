<?php
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    header('Location: index.html');
    exit;
}

$to = 'elazarwhodoesthings@gmail.com';
$subject = 'Wonder Cabinet Note';

// Sanitize inputs
$name  = htmlspecialchars(strip_tags($_POST['name'] ?? ''));
$email = filter_var($_POST['email'] ?? '', FILTER_SANITIZE_EMAIL);
$page  = htmlspecialchars(strip_tags($_POST['page'] ?? 'unknown'));
$note  = htmlspecialchars(strip_tags($_POST['note'] ?? ''));

$body  = "New note from the $page page:\n\n";
$body .= "Name:  $name\n";
$body .= "Email: $email\n";
$body .= "Page:  $page\n\n";
$body .= "Note:\n$note\n";

$headers  = "From: noreply@thiselazar.com\r\n";
$headers .= "Reply-To: $email\r\n";

$sent = mail($to, $subject, $body, $headers);
?>
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Wonder Cabinet - Note <?php echo $sent ? 'Sent' : 'Error'; ?></title>
<link rel="stylesheet" href="shared.css">
<style>
.result {
  max-width: 480px;
  margin: 80px auto;
  text-align: center;
  padding: 0 24px;
}
.result h2 {
  font-size: 13px;
  font-weight: 400;
  letter-spacing: 0.3em;
  color: #c8a86e;
  margin-bottom: 16px;
}
.result p {
  font-size: 13px;
  color: #6a6254;
  line-height: 1.6;
}
.result a {
  color: #c8a86e;
  text-decoration: none;
}
</style>
</head>
<body>
<nav class="site-nav">
  <a class="nav-brand" href="index.html">WONDER CABINET</a>
  <a href="emulator.html">EMULATOR</a>
  <a href="guide.html">FIELD GUIDE</a>
  <a href="history.html">HISTORY</a>
  <a href="order.html">ORDER</a>
</nav>
<header>
  <h1>WONDER CABINET</h1>
  <p class="tagline">A cabinet of electronic curiosities</p>
</header>
<?php if ($sent): ?>
<div class="result">
  <h2>NOTE SENT</h2>
  <p>Thanks<?php echo $name ? ', ' . $name : ''; ?>. We appreciate the feedback.</p>
  <p><a href="<?php echo $page === 'Emulator' ? 'emulator.html' : ($page === 'Field Guide' ? 'guide.html' : 'index.html'); ?>">&larr; Back to <?php echo strtolower($page); ?></a></p>
</div>
<?php else: ?>
<div class="result">
  <h2>SOMETHING WENT WRONG</h2>
  <p>Your note couldn't be sent. Please email us directly at
  <a href="mailto:elazarwhodoesthings@gmail.com">elazarwhodoesthings@gmail.com</a>.</p>
  <p><a href="<?php echo $page === 'Emulator' ? 'emulator.html' : ($page === 'Field Guide' ? 'guide.html' : 'index.html'); ?>">&larr; Try again</a></p>
</div>
<?php endif; ?>
<footer>
  Programmed with AI, Designed &amp; Curated by Hand
</footer>
</body>
</html>
