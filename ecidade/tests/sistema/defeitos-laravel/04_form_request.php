<?php
// DBFormRequest::response() e chamado pelo Laravel? FormRequest tem response()? failedValidation lanca ValidationException (medido de fato)?
require '/app/vendor/autoload.php';
use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Translation\ArrayLoader;
use Illuminate\Translation\Translator;
use Illuminate\Validation\Validator;

echo 'FormRequest::response existe: ', var_export(method_exists(FormRequest::class, 'response'), true), "\n";
echo 'DBFormRequest::response existe: ', var_export(method_exists(App\Http\Requests\DBFormRequest::class, 'response'), true), "\n";
$src = file_get_contents((new ReflectionClass(FormRequest::class))->getFileName());
echo 'chamada a $this->response( no FormRequest: ', var_export(strpos($src, '$this->response(') !== false, true), "\n";
$req = (new ReflectionClass(FormRequest::class))->newInstanceWithoutConstructor();
$url = new Illuminate\Routing\UrlGenerator(new Illuminate\Routing\RouteCollection(), Illuminate\Http\Request::create('http://localhost/x'));
$req->setRedirector(new Illuminate\Routing\Redirector($url));
$m = new ReflectionMethod(FormRequest::class, 'failedValidation');
$m->setAccessible(true);
try {
    $m->invoke($req, new Validator(new Translator(new ArrayLoader(), 'en'), [], ['a' => 'required']));
    echo "failedValidation: nao lancou\n";
} catch (\Throwable $e) {
    echo 'failedValidation lanca: ', get_class($e), ' ', substr($e->getMessage(), 0, 90), "\n";
}
