<?php

namespace App\Providers;

use Carbon\Carbon;
use Illuminate\Support\Facades\Gate;
use Illuminate\Foundation\Support\Providers\AuthServiceProvider as ServiceProvider;
use Laravel\Passport\Passport;

/**
 *
 */
class AuthServiceProvider extends ServiceProvider
{
    /**
     * The policy mappings for the application.
     *
     * @var array
     */
    protected $policies = [];

    /**
     * Passport 13 nao tem Passport::routes(): as rotas vem do provider do pacote.
     *
     * @return void
     */
    public function register()
    {
        parent::register();

        if (!method_exists(Passport::class, 'routes')) {
            config(['passport.path' => 'v4/oauth']);

            $this->app->when(\Laravel\Passport\Bridge\ClientRepository::class)
                ->needs(\Illuminate\Contracts\Hashing\Hasher::class)
                ->give(\App\Auth\SegredoClienteTextoPuro::class);
        }
    }

    /**
     * Register any authentication / authorization services.
     *
     * @return void
     */
    public function boot()
    {
        $this->registerPolicies();

        if (method_exists(Passport::class, 'routes')) {
            Passport::routes(null, [
                'prefix' => 'v4/oauth',
            ]);
        } else {
            Passport::enablePasswordGrant();
            $this->app['router']->aliasMiddleware('clientCredential', \Laravel\Passport\Http\Middleware\CheckToken::class);
        }

        Passport::tokensExpireIn(Carbon::now()->addDay());

        Passport::refreshTokensExpireIn(Carbon::now()->addDays(2));
    }
}
