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
  <h2>Note Sent</h2>
  <p>Thanks<?php echo $name ? ', ' . $name : ''; ?>. We appreciate the feedback.</p>
  <p><a href="<?php echo $page === 'Emulator' ? 'emulator.html' : ($page === 'Field Guide' ? 'guide.html' : 'index.html'); ?>">&larr; Back to <?php echo strtolower($page); ?></a></p>
</div>
<?php else: ?>
<div class="result">
  <h2>Something Went Wrong</h2>
  <p>Your note couldn't be sent. Please email us directly at
  <a href="mailto:elazarwhodoesthings@gmail.com">elazarwhodoesthings@gmail.com</a>.</p>
  <p><a href="<?php echo $page === 'Emulator' ? 'emulator.html' : ($page === 'Field Guide' ? 'guide.html' : 'index.html'); ?>">&larr; Try again</a></p>
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
