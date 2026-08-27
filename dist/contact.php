<?php
/**
 * Lead handler for the מיזוג פרו static site (Hostinger / any PHP host).
 *
 * Accepts the form on every page, emails it, and also appends it to a CSV one
 * level above public_html — so a lead is never lost to a mail failure.
 * Redirects to /thank-you/ either way; the visitor never sees a PHP page.
 */

declare(strict_types=1);

// ---------------------------------------------------------------- settings --
$TO        = 'support@mizugpro.co.il';   // where leads arrive
$FROM      = 'no-reply@mizugpro.co.il';  // must be a mailbox on this domain
$SUBJECT   = 'ליד חדש מהאתר — מיזוג פרו';
$THANKS    = '/thank-you/';
$LOG       = __DIR__ . '/../leads.csv';  // outside the web root
$MIN_SECS  = 3;                          // a human takes longer than this

// ------------------------------------------------------------------ helpers --
function finish(string $to): void {
    header('Location: ' . $to, true, 303);
    exit;
}

function clean(string $v, int $max = 500): string {
    $v = str_replace(["\r", "\n", "%0a", "%0d"], ' ', $v); // header injection
    $v = trim(strip_tags($v));
    return mb_substr($v, 0, $max);
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    finish('/');
}

// ------------------------------------------------------------- spam checks --
// bots fill hidden fields; people do not
if (!empty($_POST['website'] ?? '')) {
    finish($THANKS);
}
// and bots submit instantly
$started = (int)($_POST['started'] ?? 0);
if ($started > 0 && (time() - $started) < $MIN_SECS) {
    finish($THANKS);
}

// ----------------------------------------------------------------- payload --
$name  = clean($_POST['form_fields']['name'] ?? ($_POST['name'] ?? ''), 120);
$phone = clean($_POST['phone'] ?? '', 40);
$city  = clean($_POST['form_fields']['field_a1ac816'] ?? ($_POST['city'] ?? ''), 120);
$msg   = clean($_POST['form_fields']['field_311e598'] ?? ($_POST['message'] ?? ''), 2000);
$page  = clean($_POST['referer_title'] ?? '', 200);
$path  = clean($_POST['queried_id'] ?? '', 200);

$digits = preg_replace('/\D+/', '', $phone);
if ($name === '' || strlen((string)$digits) < 9) {
    finish('/?form=invalid');
}

$when = date('Y-m-d H:i:s');
$ip   = $_SERVER['HTTP_CF_CONNECTING_IP'] ?? $_SERVER['REMOTE_ADDR'] ?? '';

// ------------------------------------------------------------------ store ---
$row = [$when, $name, $phone, $city, $msg, $path, $page, $ip];
if ($fh = @fopen($LOG, 'a')) {
    @flock($fh, LOCK_EX);
    if (@filesize($LOG) === 0) {
        fputcsv($fh, ['תאריך', 'שם', 'טלפון', 'עיר', 'הודעה', 'עמוד', 'כותרת', 'IP']);
    }
    fputcsv($fh, $row);
    @flock($fh, LOCK_UN);
    fclose($fh);
}

// ------------------------------------------------------------------- mail ---
$body = "ליד חדש מהאתר\n\n"
      . "שם:      {$name}\n"
      . "טלפון:   {$phone}\n"
      . "עיר:     {$city}\n"
      . "הודעה:   {$msg}\n\n"
      . "מהעמוד:  {$path}\n"
      . "כותרת:   {$page}\n"
      . "התקבל:   {$when}\n";

$headers = implode("\r\n", [
    'MIME-Version: 1.0',
    'Content-Type: text/plain; charset=UTF-8',
    'Content-Transfer-Encoding: 8bit',
    'From: מיזוג פרו <' . $FROM . '>',
    'Reply-To: ' . $FROM,
    'X-Mailer: mizugpro-static',
]);

@mail($TO, '=?UTF-8?B?' . base64_encode($SUBJECT) . '?=', $body, $headers, '-f' . $FROM);

finish($THANKS);
