import chai from 'chai';
import chaiHttp from 'chai-http';
import { createApp, generateShortUrlBitwise, generateShortUrlMD5, generateShortUrlSHA256,  generateShortUrlMurmurBase64Url, generateShortUrlMurmurInt } from '../url_shortener';
import { Server } from 'http';

chai.use(chaiHttp);
const { expect } = chai;

const requestCount = 2000;
const testTimeout = 10000;
const randomUrlLength = 2000;
const domain = "https://a.b/"
const subdomain = "path?-._~!$&'()*+,;=:@#a";
const testUrl = `${domain}${subdomain}`;
const domainLength = domain.length;

function getRandomUrl(): string {
    const randomStringLength = randomUrlLength - domainLength;
    const characters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._~!$&\'()*+,;=:@';
    let randomString = '';
    for (let i = 0; i < randomStringLength; i++) {
        const randomIndex = Math.floor(Math.random() * characters.length);
        randomString += characters[randomIndex];
    }

    return `${domain}${randomString}`;
}

describe('getRandomUrl', () => {
    it('should generate a URL of the correct total length', () => {
        const url = getRandomUrl();
        expect(url.length).to.equal(randomUrlLength);
    });

    it('should generate a valid URL', () => {
        const url = getRandomUrl();
        console.log(`[LOG] Random URL: ${url}`);
        const urlPattern = new RegExp(
            `^${domain.replace('.', '\\.')}[a-zA-Z0-9\\-._~!$&'()*+,;=:@]{${randomUrlLength - domainLength}}$`
        );
        expect(url).to.match(urlPattern);
    });

    it('should generate unique URLs on multiple calls', () => {
        const generatedUrls = new Set();
        for (let i = 0; i < 100; i++) { // Generate a smaller number to avoid excessive computation
            const url = getRandomUrl();
            generatedUrls.add(url);
        }
        expect(generatedUrls.size).to.equal(100);
    });
});

describe('URL Shortener API', () => {
    describe('Bitwise Shortener', () => {
        let serverBitwise: Server;
        let portBitwise: number;

        // Start the Bitwise hashing server before tests
        before((done) => {
            const { app } = createApp(generateShortUrlBitwise);
            serverBitwise = app.listen(0, () => {
                portBitwise = (serverBitwise.address() as any).port;
                console.log(`[LOG] Bitwise Test server running on port ${portBitwise}`);
                done();
            });
        });

        // Close the Bitwise hashing server after tests
        after((done) => {
            serverBitwise.close(() => {
                console.log('[LOG] Bitwise Test server closed');
                done();
            });
        });

        it('should return 400 if longURL is not provided (Bitwise)', async () => {
            const res = await chai.request(`http://localhost:${portBitwise}`).post('/shorten').send({});
            expect(res).to.have.status(400);
            expect(res.text).to.equal('longURL is required');
        });

        it('should generate different short URLs for different long URLs (Bitwise)', async () => {
            const url1 = `${testUrl}-1`;
            const url2 = `${testUrl}-2`;

            const res1 = await chai.request(`http://localhost:${portBitwise}`).post('/shorten').send({ longURL: url1 });
            const res2 = await chai.request(`http://localhost:${portBitwise}`).post('/shorten').send({ longURL: url2 });

            expect(res1).to.have.status(200);
            expect(res2).to.have.status(200);
            expect(res1.body.shortURL).to.not.equal(res2.body.shortURL);
        });

        it('should generate the same short URL for the same long URL (Bitwise)', async () => {
            const url = testUrl;

            const res1 = await chai.request(`http://localhost:${portBitwise}`).post('/shorten').send({ longURL: url });
            const res2 = await chai.request(`http://localhost:${portBitwise}`).post('/shorten').send({ longURL: url });

            expect(res1).to.have.status(200);
            expect(res2).to.have.status(200);
            expect(res1.body.shortURL).to.equal(res2.body.shortURL);
        });

        it('should generate a short URL that matches the expected pattern (Bitwise)', async () => {
            const url = testUrl;
            const res = await chai.request(`http://localhost:${portBitwise}`).post('/shorten').send({ longURL: url });

            expect(res).to.have.status(200);
            expect(res.body).to.have.property('shortURL');
            const shortURLPattern = new RegExp(`^http://localhost:${portBitwise}/[a-zA-Z0-9]+$`);
            const shortURL = res.body.shortURL as string;
            console.log(`[LOG] '${url}' --> '${shortURL}'`);
            expect(shortURL).to.match(shortURLPattern);
        });

        it('should log the average call time for many requests (Bitwise)', async function () {
            this.timeout(testTimeout); // Increase timeout for this test

            const url = testUrl;
            const startTime = Date.now();

            for (let i = 0; i < requestCount; i++) {
                await chai.request(`http://localhost:${portBitwise}`).post('/shorten').send({ longURL: url });
            }

            const endTime = Date.now();
            const averageTime = (endTime - startTime) / requestCount;
            console.log(`[LOG] Average call time for ${requestCount} requests (Bitwise): ${averageTime} ms`);
        });

        it('should log the average call time for many requests with randomized URLs (Bitwise)', async function () {
            this.timeout(testTimeout); // Increase timeout for this test

            const startTime = Date.now();

            for (let i = 0; i < requestCount; i++) {
                const url = getRandomUrl();
                await chai.request(`http://localhost:${portBitwise}`).post('/shorten').send({ longURL: url });
            }

            const endTime = Date.now();
            const averageTime = (endTime - startTime) / requestCount;
            console.log(`[LOG] Average call time for ${requestCount} requests with randomized URLs (Bitwise, length ${randomUrlLength}): ${averageTime} ms`);
        });
        
        it('should two URLs with the same hash (bitwise) should generate different short URLs', async () => {
            const url = `https://example.com/BhYT5l~E1Dcjn:a5*KjdU*USZw+gWOpQ2sek:TN'T)xb_CfvoJYw7t2.x5a~gd1.W4:qB8RSQMy1P,Pzr,(Ou'wX'Np,gb3G;E(=xKCfKjGHG633:*~MAMQ$RDi~m)nPt5uG*m(eqMH3Vzwoi.qQ$Xu7HB;MH$CHjl)&2WKEnK7.,SPG$jzKmeo_g~Eg3+qp*eOJ&cmiG7p!wwDO2LH-Xu52q9Bo~mE*x('~cSi2K_lJwg~LbkI1jSwK(pm'+0GlErV,pxClqy!Ym,C$2Jv1Jo95eEI~@r!HOJhd3FvAc~=l3o-OlZgOq&)AkW(HI.E_Rgi2)f1zkV7YV3@dwk)v*2_qz+Hr*mPPgb*'m7Pk.'Dj9y'pkbj*LRd~8)y'_*v!DHLtbkQ1S~~)Avuy+3dK*h)!KTmCa3MBbtaxR$$xu2sWs=HAE4TEpEnB3qf;'tD$h4:AVXcTTzdtJ05*A9h3=S(v1GSlZgp3S'2qUP=gZYq&qvHiPnJb&IQ'v,(fnREm_(~,;9nOxFiI,YRuWnuVc!WI3zY:=X'ras_wuLhp-_$VXPQkz*_n(si$KPe&=e,a__asC8CfblA:wsAN5,ar:aG;xmtQ+baPKJ,&uDK_1)F;4Cu~WNzL9S!,U(22Y&zme5d:AG)nQ1!dQ:GdaG0A=qYz4T:2ITUti2DP+:!mlq0pLWk_v'~o_NSASL9kR;p(T9o.3&hkGU,3GszF=$=AvFC7j$Mdz:3um+l-hvETIed3slH2wKb&():72v3glALH9orz(IKzt2u1Y~;l9'sjQ;*J;)K=vJWsFrSuvJJo09hPVIqj0qg3eBRmcOJauSgAuLEP6KsUpC'sFQpUnhlnxH=e+wTJeOsU+UiRSsYYh_utOtLC23KH64Vb(U5!!p0'jt&:jVj~le'jj~q~$K9ctoOFz_46frsFqSEreWsf43H~)mvFN0id:q,+63lZ.ohnxcAaVvV,L~arfo!8A,$;66,gDYKD0KBolSHzv.qIp1O&D~6YQLFRUv*aNnahn=oI6LRk~_'Ka3@jTiv9EqjH6'.PKB8xau;a3qjcagtcu0&piG,:RjeIV8:uOJni9ERh'3YYUpbv4ao$a(RKsI8'9IU&ZNkq62EMah6aWk-,syg+.+QsjqFvxz=0acgnS_2LXkbh'*FyKOQ3I@)$jrCcI4+Jq:UJHS3Lk,iRG6m5E$cNOrSGY'HW7T*ArspGv~$BQ4WsYNBx6jXVNfoq:7o2WjGDQ4L2'0AHkv9(:peL4y2HL9'Fha99d3co0)Gm_Rj56.qCi9':zx'CY.pZ@~u6NTp'&~$kpl;fE*7~xgeY$.c-U=zt!_B,imJSq)W8FprNg,yZVz7EiDjK1z,),'cAw=KZm-e+IbC0nP=ft6K+V,uuY-QsWV@GvYjU!::m9_x-SPWDLL4wl,ovJIB(CauU1jTF=*'f*gm0zj7:)+4*68e~Szo9EA4~51A,0yoX=7k$1_Req9IJUnTt3p~X9Ue54Q)*Bis-Xm4tI0UOkclse=iL,lJ9HytXQ7j(a-L*bO9MyTIr5p=)k!0;~~!6JftI~69,;jphE-Y+7:nGZ1unfoX)r7:PZz$=~eMRdR=~lEbpE=y*3$JL6i0n-T''Z(:g22&l$KcQ5+xq@@1ltdSi.*vcBSNMY+$kVi9On'WV!~hs+xLSoBR;v,,cmtzvYxP.)$MJMU0A$EE+-p6o6'hDRGDMPhptm$fqIQ!=WJh5+d:yj(vg.a79r:r+:BN1Jbo3D(@f8NjIt$19v~rn((gTJG8A8Ng3n)_dlIhubM_mguEe83BwR1jR'1Xv')(U172&!mxHQX+P_m$UfdIeXfjiBS+Xy7s4tXk&mX&n==&J'E2EBv:xkUXqqaN4mBq=D;)IcC*O'*u!y@=eI4:;C'p2EW.pt;Gqu7ZIWE;:&zB4laB_MfD(9O1c-ur8lCp0s$a8;r;Ah.Bos8MZ'-z6PiUuUbg-OB9G:!Obvt,0Ty9x`;
            const url2 = `https://example.com/'Y6QFKEx_z;Tu(6im9nR1qoZx,A2:mJ&IEj5lP8Wevm9Su3idIWW3O@!PX~8wNSw*gXY-eUwgA5By!(iVWnucZiuNdt_4Z5HiB&fMqA~U9IQ@$C&1Ej&a:0,*TVzZbjjx.hrtdxaX*)A.c01sOdAa(:r=ZCNp4CgI-C(8XWEIyHrAY7xmCS:S46_k@Qvs.~jY-S1:4p5f6,&CJP@2=1H:Sj,;Ar;G3~xq&O~g_$_OpqVs7g)&.Rtj3KN-vbMcoU3Hd~oU+(+wf'PAZAF9b@ed@Z2&(fS=~(gqY+0bYG8M-SttQVlm2A-EIAEI55JKzcxh,4qeJmJ-F3rQrIjb1P*L4rohdGxnc:&kP&n3PF2Otq~:&dzQf81W~CfPEGP3Jm5$d7.nncbIq5guEUE@iD@f4W.l+hzJUWmfE;U8(G(cx7R-;geEtHH$aw.$$o~ajuoPv1hZK8k_x38tSNtL:!fuKcjd7*H$)g$yvrGBP.9T_zK!_5xCy~c@AM=yGJ$m2Xo$nEMgwzoXYy8PuI~=OMyGZnUQovuRg6aZcuM1wFdodoDZyaj:40FAN6xxkA0BR)7@YO03+aM1,G*bv~ZH4zV@5LXOpYhf3$mBNsrXz_;h01E!J(J+YOiCr'xYO1$k61F7FwYF~2-dZK,E&Z65cyNq,BZygjX-0C4ur+m&f-Mq.ec;YpBc'0Tu8b6v7*9Z=r$!8&M6H9OF+s&.bHSViTn9)nsfLK)xhCw(SW@+hl~~ZRhK.gKG+.9'or~oc)RNHMVFG697.qQOfk(s33$QY)vFED0WX+eeV9!Gxf1$W5@.;MxxC228sMg57:_TpXmiDzH1Y_z=l$T+GP!lgx);8rJI9*HeHc&!U(Uv&P8)_WD7w6;pa4s8,P'.HkerD,;70jsLFbv4HAuOk=K6JnH7PT-aps~~bLQ6FKPN5t9o4,hP&B-4+fNEIyD!OD=L@@)ew9bL=RF_3dQ7-9E)-yFTro3)&N..TG@u.o(yXmdzjsVZ'c_HS7V_NZRJjANJEmPoEy3+3dWY0_VN_AI&ff3v(En@(73+ieim'_vCm8FE0i-a!U6N_;SpvVyE1BE'LTe2~y&r$XY68dn!4l!*QWBqxuI3xhw(-=IZ4rRm64-n=ke-;I;UkyOS1h2o_hl'DH!YJi=:CKMME=)6ws+w~i8MPuQwf=n)Tcnc9t&)*fZsW~F=)(;SO+UoS-P_UjNlC$zt9IkIW~ZhZBs4k73dpOCB*YCKXIhm0f!~6@E1d2pUU,G~auv;9Yi;V_xAK9Y&dhQC!BcJ&sBJAa3R),,8d$U!3@'V+~6!WSJzuhUK+7oSe:EJR_ZC4gMSi6BrC5s=XC3@Fgq)-EcZo.3XmTT6X~!XYOg_ojJ!~*mz*4Ow$4!RFrWgGR$P+@vpGMI';Q1Af930JI(I1grvK+u5Z'TgkstF=2un4G3cMPC9.jxK&NMktzBzd3'k6;AT94P&PghgRHJ!J;3rmHltk8+5f=EMQ3ZQ)5D*NfDwdN&-mN!6)jvvw0+K@d7Fn4R)2wIq-A6bBrm5bYz-+iqLSi)nlc@k)1R3,.sH;jsDO:7+ig+5pmzi3*Aq74Lf_@=vgy+0&=1Cv)2PXOWw'fjn.fSq8_iuk7OEKv&1@'.acSExPeBlrI7a'gqhN~fNZWPdnc*eB17mc1:Ke2Zf+y3!on0DM.gr4;dsz!q_!3~RY5&Ds2hmfqm:=f1M.9oll;)FZ!HLx,R8.U$wpnFt:+KLbL$7heWheggyd:4ta(yyx7k!UxN:p*WV;i,w_OUY=cJ@8jK!b&5mO_x6nT.+Q-JOV&ud+K'8~$*(Y_vsQL)oE:MWV+5_5o.g;+YD7@9V..xgwNCc-4-bgulD+Lf&Sf4Q'TUJmNF+k6OLbX0IO)lEGX&ATTsX*rC1O3;UfOG7l&Wyj;4e4ROyONgC0K=f!x,*+Edfp7*Y.X37i1eh:LnZYlV$al)1~=H~Ml23C@pg:m8.JIYh8!xVIxL`;
            const res1 = await chai.request(`http://localhost:${portBitwise}`).post('/shorten').send({ longURL: url });
            const res2 = await chai.request(`http://localhost:${portBitwise}`).post('/shorten').send({ longURL: url2 });
            expect(res1.body.shortURL).to.not.equal(res2.body.shortURL);
        });
    });

    describe('MD5 Shortener', () => {
        let serverMD5: Server;
        let portMD5: number;

        // Start the MD5 hashing server before tests
        before((done) => {
            const { app } = createApp(generateShortUrlMD5);
            serverMD5 = app.listen(0, () => {
                portMD5 = (serverMD5.address() as any).port;
                console.log(`[LOG] MD5 Test server running on port ${portMD5}`);
                done();
            });
        });

        // Close the MD5 hashing server after tests
        after((done) => {
            serverMD5.close(() => {
                console.log('[LOG] MD5 Test server closed');
                done();
            });
        });

        it('should return 400 if longURL is not provided (MD5)', async () => {
            const res = await chai.request(`http://localhost:${portMD5}`).post('/shorten').send({});
            expect(res).to.have.status(400);
            expect(res.text).to.equal('longURL is required');
        });

        it('should generate different short URLs for different long URLs (MD5)', async () => {
            const url1 = `${testUrl}-1`;
            const url2 = `${testUrl}-2`;

            const res1 = await chai.request(`http://localhost:${portMD5}`).post('/shorten').send({ longURL: url1 });
            const res2 = await chai.request(`http://localhost:${portMD5}`).post('/shorten').send({ longURL: url2 });

            expect(res1).to.have.status(200);
            expect(res2).to.have.status(200);
            expect(res1.body.shortURL).to.not.equal(res2.body.shortURL);
        });

        it('should generate the same short URL for the same long URL (MD5)', async () => {
            const url = testUrl;

            const res1 = await chai.request(`http://localhost:${portMD5}`).post('/shorten').send({ longURL: url });
            const res2 = await chai.request(`http://localhost:${portMD5}`).post('/shorten').send({ longURL: url });

            expect(res1).to.have.status(200);
            expect(res2).to.have.status(200);
            expect(res1.body.shortURL).to.equal(res2.body.shortURL);
        });

        it('should generate a short URL that matches the expected pattern (MD5)', async () => {
            const url = testUrl;
            const res = await chai.request(`http://localhost:${portMD5}`).post('/shorten').send({ longURL: url });

            expect(res).to.have.status(200);
            expect(res.body).to.have.property('shortURL');
            const shortURLPattern = new RegExp(`^http://localhost:${portMD5}/[a-zA-Z0-9-_]+$`);
            const shortURL = res.body.shortURL as string;
            console.log(`[LOG] '${url}' --> '${shortURL}'`);
            expect(shortURL).to.match(shortURLPattern);
        });

        it('should log the average call time for many requests (MD5)', async function () {
            this.timeout(testTimeout); // Increase timeout for this test

            const url = testUrl;
            const startTime = Date.now();

            for (let i = 0; i < requestCount; i++) {
                await chai.request(`http://localhost:${portMD5}`).post('/shorten').send({ longURL: url });
            }

            const endTime = Date.now();
            const averageTime = (endTime - startTime) / requestCount;
            console.log(`[LOG] Average call time for ${requestCount} requests (MD5): ${averageTime} ms`);
        });

        it('should log the average call time for many requests with randomized URLs (MD5)', async function () {
            this.timeout(testTimeout); // Increase timeout for this test

            const startTime = Date.now();

            for (let i = 0; i < requestCount; i++) {
                const url = getRandomUrl();
                await chai.request(`http://localhost:${portMD5}`).post('/shorten').send({ longURL: url });
            }

            const endTime = Date.now();
            const averageTime = (endTime - startTime) / requestCount;
            console.log(`[LOG] Average call time for ${requestCount} requests with randomized URLs (MD5, length ${randomUrlLength}): ${averageTime} ms`);
        });
    });
    
    describe('SHA256 Shortener', () => {
        let serverSHA256: Server;
        let portSHA256: number;

        // Start the SHA256 hashing server before tests
        before((done) => {
            const { app } = createApp(generateShortUrlSHA256);
            serverSHA256 = app.listen(0, () => {
                portSHA256 = (serverSHA256.address() as any).port;
                console.log(`[LOG] SHA256 Test server running on port ${portSHA256}`);
                done();
            });
        });

        // Close the SHA256 hashing server after tests
        after((done) => {
            serverSHA256.close(() => {
                console.log('[LOG] SHA256 Test server closed');
                done();
            });
        });

        it('should return 400 if longURL is not provided (SHA256)', async () => {
            const res = await chai.request(`http://localhost:${portSHA256}`).post('/shorten').send({});
            expect(res).to.have.status(400);
            expect(res.text).to.equal('longURL is required');
        });

        it('should generate different short URLs for different long URLs (SHA256)', async () => {
            const url1 = `${testUrl}-1`;
            const url2 = `${testUrl}-2`;

            const res1 = await chai.request(`http://localhost:${portSHA256}`).post('/shorten').send({ longURL: url1 });
            const res2 = await chai.request(`http://localhost:${portSHA256}`).post('/shorten').send({ longURL: url2 });

            expect(res1).to.have.status(200);
            expect(res2).to.have.status(200);
            expect(res1.body.shortURL).to.not.equal(res2.body.shortURL);
        });

        it('should generate the same short URL for the same long URL (SHA256)', async () => {
            const url = testUrl;

            const res1 = await chai.request(`http://localhost:${portSHA256}`).post('/shorten').send({ longURL: url });
            const res2 = await chai.request(`http://localhost:${portSHA256}`).post('/shorten').send({ longURL: url });

            expect(res1).to.have.status(200);
            expect(res2).to.have.status(200);
            expect(res1.body.shortURL).to.equal(res2.body.shortURL);
        });

        it('should generate a short URL that matches the expected pattern (SHA256)', async () => {
            const url = testUrl;
            const res = await chai.request(`http://localhost:${portSHA256}`).post('/shorten').send({ longURL: url });

            expect(res).to.have.status(200);
            expect(res.body).to.have.property('shortURL');
            const shortURLPattern = new RegExp(`^http://localhost:${portSHA256}/[a-zA-Z0-9-_]+$`);
            const shortURL = res.body.shortURL as string;
            console.log(`[LOG] '${url}' --> '${shortURL}'`);
            expect(shortURL).to.match(shortURLPattern);
        });

        it('should log the average call time for many requests (SHA256)', async function () {
            this.timeout(testTimeout); // Increase timeout for this test

            const url = testUrl;
            const startTime = Date.now();

            for (let i = 0; i < requestCount; i++) {
                await chai.request(`http://localhost:${portSHA256}`).post('/shorten').send({ longURL: url });
            }

            const endTime = Date.now();
            const averageTime = (endTime - startTime) / requestCount;
            console.log(`[LOG] Average call time for ${requestCount} requests (SHA256): ${averageTime} ms`);
        });

        it('should log the average call time for many requests with randomized URLs (SHA256)', async function () {
            this.timeout(testTimeout); // Increase timeout for this test

            const startTime = Date.now();

            for (let i = 0; i < requestCount; i++) {
                const url = getRandomUrl();
                await chai.request(`http://localhost:${portSHA256}`).post('/shorten').send({ longURL: url });
            }

            const endTime = Date.now();
            const averageTime = (endTime - startTime) / requestCount;
            console.log(`[LOG] Average call time for ${requestCount} requests with randomized URLs (SHA256, length ${randomUrlLength}): ${averageTime} ms`);
        });
    });
    
    describe('MurmurHashBase64Url Shortener', () => {
        let serverMurmurHashBase64Url: Server;
        let portMurmurHashBase64Url: number;

        // Start the MurmurHashBase64Url hashing server before tests
        before((done) => {
            const { app } = createApp(  generateShortUrlMurmurBase64Url);
            serverMurmurHashBase64Url = app.listen(0, () => {
                portMurmurHashBase64Url = (serverMurmurHashBase64Url.address() as any).port;
                console.log(`[LOG] MurmurHashBase64Url Test server running on port ${portMurmurHashBase64Url}`);
                done();
            });
        });

        // Close the MurmurHashBase64Url hashing server after tests
        after((done) => {
            serverMurmurHashBase64Url.close(() => {
                console.log('[LOG] MurmurHashBase64Url Test server closed');
                done();
            });
        });

        it('should return 400 if longURL is not provided (MurmurHashBase64Url)', async () => {
            const res = await chai.request(`http://localhost:${portMurmurHashBase64Url}`).post('/shorten').send({});
            expect(res).to.have.status(400);
            expect(res.text).to.equal('longURL is required');
        });

        it('should generate different short URLs for different long URLs (MurmurHashBase64Url)', async () => {
            const url1 = `${testUrl}-1`;
            const url2 = `${testUrl}-2`;

            const res1 = await chai.request(`http://localhost:${portMurmurHashBase64Url}`).post('/shorten').send({ longURL: url1 });
            const res2 = await chai.request(`http://localhost:${portMurmurHashBase64Url}`).post('/shorten').send({ longURL: url2 });

            expect(res1).to.have.status(200);
            expect(res2).to.have.status(200);
            expect(res1.body.shortURL).to.not.equal(res2.body.shortURL);
        });

        it('should generate the same short URL for the same long URL (MurmurHashBase64Url)', async () => {
            const url = testUrl;

            const res1 = await chai.request(`http://localhost:${portMurmurHashBase64Url}`).post('/shorten').send({ longURL: url });
            const res2 = await chai.request(`http://localhost:${portMurmurHashBase64Url}`).post('/shorten').send({ longURL: url });

            expect(res1).to.have.status(200);
            expect(res2).to.have.status(200);
            expect(res1.body.shortURL).to.equal(res2.body.shortURL);
        });

        it('should generate a short URL that matches the expected pattern (MurmurHashBase64Url)', async () => {
            const url = testUrl;
            const res = await chai.request(`http://localhost:${portMurmurHashBase64Url}`).post('/shorten').send({ longURL: url });

            expect(res).to.have.status(200);
            expect(res.body).to.have.property('shortURL');
            const shortURLPattern = new RegExp(`^http://localhost:${portMurmurHashBase64Url}/[a-zA-Z0-9-_]+$`);
            const shortURL = res.body.shortURL as string;
            console.log(`[LOG] '${url}' --> '${shortURL}'`);
            expect(shortURL).to.match(shortURLPattern);
        });

        it('should log the average call time for many requests (MurmurHashBase64Url)', async function () {
            this.timeout(testTimeout); // Increase timeout for this test

            const url = testUrl;
            const startTime = Date.now();

            for (let i = 0; i < requestCount; i++) {
                await chai.request(`http://localhost:${portMurmurHashBase64Url}`).post('/shorten').send({ longURL: url });
            }

            const endTime = Date.now();
            const averageTime = (endTime - startTime) / requestCount;
            console.log(`[LOG] Average call time for ${requestCount} requests (MurmurHashBase64Url): ${averageTime} ms`);
        });

        it('should log the average call time for many requests with randomized URLs (MurmurHashBase64Url)', async function () {
            this.timeout(testTimeout); // Increase timeout for this test

            const startTime = Date.now();

            for (let i = 0; i < requestCount; i++) {
                const url = getRandomUrl();
                await chai.request(`http://localhost:${portMurmurHashBase64Url}`).post('/shorten').send({ longURL: url });
            }

            const endTime = Date.now();
            const averageTime = (endTime - startTime) / requestCount;
            console.log(`[LOG] Average call time for ${requestCount} requests with randomized URLs (MurmurHashBase64Url, length ${randomUrlLength}): ${averageTime} ms`);
        });
    });
    
    describe('MurmurHashInt Shortener', () => {
        let serverMurmurHashInt: Server;
        let portMurmurHashInt: number;

        // Start the MurmurHashInt hashing server before tests
        before((done) => {
            const { app } = createApp(  generateShortUrlMurmurInt);
            serverMurmurHashInt = app.listen(0, () => {
                portMurmurHashInt = (serverMurmurHashInt.address() as any).port;
                console.log(`[LOG] MurmurHashInt Test server running on port ${portMurmurHashInt}`);
                done();
            });
        });

        // Close the MurmurHashInt hashing server after tests
        after((done) => {
            serverMurmurHashInt.close(() => {
                console.log('[LOG] MurmurHashInt Test server closed');
                done();
            });
        });

        it('should return 400 if longURL is not provided (MurmurHashInt)', async () => {
            const res = await chai.request(`http://localhost:${portMurmurHashInt}`).post('/shorten').send({});
            expect(res).to.have.status(400);
            expect(res.text).to.equal('longURL is required');
        });

        it('should generate different short URLs for different long URLs (MurmurHashInt)', async () => {
            const url1 = `${testUrl}-1`;
            const url2 = `${testUrl}-2`;

            const res1 = await chai.request(`http://localhost:${portMurmurHashInt}`).post('/shorten').send({ longURL: url1 });
            const res2 = await chai.request(`http://localhost:${portMurmurHashInt}`).post('/shorten').send({ longURL: url2 });

            expect(res1).to.have.status(200);
            expect(res2).to.have.status(200);
            expect(res1.body.shortURL).to.not.equal(res2.body.shortURL);
        });

        it('should generate the same short URL for the same long URL (MurmurHashInt)', async () => {
            const url = testUrl;

            const res1 = await chai.request(`http://localhost:${portMurmurHashInt}`).post('/shorten').send({ longURL: url });
            const res2 = await chai.request(`http://localhost:${portMurmurHashInt}`).post('/shorten').send({ longURL: url });

            expect(res1).to.have.status(200);
            expect(res2).to.have.status(200);
            expect(res1.body.shortURL).to.equal(res2.body.shortURL);
        });

        it('should generate a short URL that matches the expected pattern (MurmurHashInt)', async () => {
            const url = testUrl;
            const res = await chai.request(`http://localhost:${portMurmurHashInt}`).post('/shorten').send({ longURL: url });

            expect(res).to.have.status(200);
            expect(res.body).to.have.property('shortURL');
            const shortURLPattern = new RegExp(`^http://localhost:${portMurmurHashInt}/[a-zA-Z0-9-_]+$`);
            const shortURL = res.body.shortURL as string;
            console.log(`[LOG] '${url}' --> '${shortURL}'`);
            expect(shortURL).to.match(shortURLPattern);
        });

        it('should log the average call time for many requests (MurmurHashInt)', async function () {
            this.timeout(testTimeout); // Increase timeout for this test

            const url = testUrl;
            const startTime = Date.now();

            for (let i = 0; i < requestCount; i++) {
                await chai.request(`http://localhost:${portMurmurHashInt}`).post('/shorten').send({ longURL: url });
            }

            const endTime = Date.now();
            const averageTime = (endTime - startTime) / requestCount;
            console.log(`[LOG] Average call time for ${requestCount} requests (MurmurHashInt): ${averageTime} ms`);
        });

        it('should log the average call time for many requests with randomized URLs (MurmurHashInt)', async function () {
            this.timeout(testTimeout); // Increase timeout for this test

            const startTime = Date.now();

            for (let i = 0; i < requestCount; i++) {
                const url = getRandomUrl();
                await chai.request(`http://localhost:${portMurmurHashInt}`).post('/shorten').send({ longURL: url });
            }

            const endTime = Date.now();
            const averageTime = (endTime - startTime) / requestCount;
            console.log(`[LOG] Average call time for ${requestCount} requests with randomized URLs (MurmurHashInt, length ${randomUrlLength}): ${averageTime} ms`);
        });
        
        it('should two URLs with the same hash (MurmurHashInt) should generate different short URLs', async () => {
            const url = `https://example.com/Ap1;QQXX6(m-mUskpFA1_nxY,_'B@V$0$FdD;tqkH2@RL:W)8zvxK0~a4S:2amP_YLMtc+tO1bEywh7bmzTsIR'M(K4)hMQLUYk.-t5R!_bKw(J+ls1rnE&_S8ZhH7xsMJz$M(LUlzj,c,WnzdSL8F7wz.(Hp)$oK)wdsQ~MvUbJXqMi9CSYYe1y-&*'$L',zkG$(7+GTs7UHu415u2.YtE;vXxg!1,;h-ZSCHP8kb8mU4gzWiF!,=8LDoI)cvhr1v=wnSZ._ff;G6;n+*dGAKueT.=*!q$KL;tsSgOW!myiw=4L3T0Voj2;H;c.PL0Y9V,E;B@fXbwiEPY9o!)rawADna)m:Ea$=~x1;2=Gn8o-s+;a+jq~.h=kFGMve6n~BGYkK1EQwscLey1:muE1+gtq&H$oo12$!nMMLHshYpAfWV9CYMAxrcChmYY.M_Ubcut37Wa3X.Qs8vKaICo(tqXxo9c@*O0JPKk8$vq*)JA=40S4S'$3@M,lbr)rRixvL$NiQwIEdxG9Rx47'pEwR,&Bg&hF)i-y4G1icD5UK-lAgxsC&UEaBn.7TbHO.cY4gllIPL+VsdnXzesKV:U9IZ'P-l+=+PdU$IoBuAS$hDW_;19GRS*Oo7W(2thweFeL$uIf'IfX,p9lEPu:+c=gu32*MJaekma!9oyKlsJ!&vapfJlMq@CbS$;'mdV-f)jBu.F$Jf~*c3cAasKK0f(WwAhX587X'y=B~Nwh)lYcXRv!BKUNuP-'Z.a(9naOoS&Xi.aZoGU'bI=DQzVc0&jfO)jeZ@,oXb.zdo*7iG0!3aa_L@G9p&rk:(HQLaR&YgvspyA!5Z.Leb+Qi=zq=Uqnhbr3Cj~VmtiPK1b;xK(.T7=dJWmv38opcx(Q9RJ.Ds323C&QAWFRDs4y3-,B724)@UKm4=g:bcFBV~_SAEYf$$A1GGlOUI+Mm~GmsytiuHf's'4xere,usxB4ggT!9S0_F)q'lu2v5ab_&@W~MJ5z4S4e(Hgr,_nL)x!;-6$PH6TQ(!;MrPNqY*cvMkWS(nVRKiqOhhOp=0pVOtV,5D3y-UW5hGa&R0_rFDo8oXrpgK'!Osvb_3!z*U)XxOu:4E:TIA1Jm.2p=92ntAsN_;N~N2wms(pd1E4.FMT0S6YEV$!&2-uMl9l$PRX5RfW&$Quts0Fgv9rU'j~DYCei8Vv4QMYf&y&IjZrZ8)BkJc7Zk.p10M(f2:Mkb,NRfIup~xF0P*,M&gXe=N65XmXrt4'k9QKbog5*(*GXdX'co3CbaG_Ln-*J3MQ:ghJUi'X;2xv)9SZg~Hqj&&dsWk&)+G.@.Fk$lvp!+-bSqq4n:XZ,3~7diF4Ad=~d2@fh!gUe5s'Z.A=b36d,Jp)to~2R.&$AynXjz6@2i)K-qn&*nv=.rfY+_mHPiTCr35Wrv(xf1x5zcoR;l=YKCs2g;f(Kt6E~wV-Ek&G'RW$h+IuvSziPE:mk4b05W$NY&c=:)cMVLU1I*bM=rMq5B0Erot,FDtjq.f!fw,H@luHAyTq=_DPCUjFfr@-5y4C,D-dMBXB_vwEeavUe4jT+49~h8GCvyjCx+:5;HVhzZEiSy*K8hM*g!IPhnBU5O+2t0Xxj+N@AkKK=&c;K5As0gt1MEOX'zwRA3*oUGSj+8BaZQrIvQG10IrL'G&4D3+6zAcYlZ*EPnDc+N0wmDA@bqI4=sf!cs*.fxpj*FRP7wK_0,=Zjkl'Sk!50EvTcHFVIfzYM+oqFGIFmFJ*jHZqz5$FgrwIh=K&&4Q=lcA0_9LM.mzkF&';aa;7-5G)73oeY$Qd.5oJfIz9N:sp3dneDcS(dN(ZvwD_0r(8Nca;:wBEq'L~(d-+A36,FWA4R5WiO@Voc_iX:8A*KWyCmk'1rqV0M'SoGq=QXxAR4PA*gapEb.n6Z7io$(mjn.zF7s&i:@@d$;x9p)EubPqr,0bXy9v,ufJ9bV_@.ugGn:7=DnX)2QMqqJ$M`;
            const url2 = `https://example.com/EhJEIW)VlCq8;~LQKIV7FKpbXJj'870BFuZ!o3:9$5('&YUJN6Q9+mS.U(5mCR*JoWv_3h6CkSMHUTcg)y1r4c3zWw@5qtiOW84BnxOps'$cA3Bj&jRzxhIbGJTmYmra:y0*lc4c,LRvw+Y-~enXhKVTP..BtTyNXTmP=Zn)F1V*U.+_!5bXa'hioiw_D2lNi_(_5.P7sARStagmo_ttoya5Rv2Hx=QnvBCR77ZYMDzy_,a6&8fJAMm=BWWdsem1s94aIFsr+O3qdC_i@FMWCfuKe'9:.6:VG=ZBbZeV2xH)*W0~__2P!n(:Hi_j8E;NeM3NjvGxf=q_ZQDk7ze0=84Up~6R1v_ut&uo-n::b1xOu;rlcXZF,x_u:xES=xdRW~nO6Y6eI2X4Z*x@k-5l;aX7I2czdVxDLmf'(-)l~JE+fPJnu97hBU(lDt('+Y5wMM8CUxxfKKu+5t1Qv4w_O-.J7*QE!+kDFgQ=sDu:Bl-7JKs0=C6Kt7P6xmSj,,W;DzeoxjwYbq9F2nj.ESlrohuc(Y$H&1H~'=f7'*3@qTn3(j;&A0m2)iL9BH~_g)L&'3@$L$'fbk4(4C'ZkHsc@p,BmZp~fOxT8v,Cz3E7&N3+n*4X-;&am7:(ah6AX_XXDJpe.Z1V)6'vF+M8Z$Y!~TOVn.WUI5HFVe:eQ&Yl1i8Xhot3kFa:5c@d=v!g@hL5rj-;@9SVZ6zNs$G@cQrz2zzTD-YdHG.b-73fLD$pElX7WZN(H_Uoq9=O8upd;&PL;1,V0'NJWlLNV1ek+D;,wlfq!LjiP82,'M_2r~Qj06nOgs!sO+kJ8Rb4P::om&Wq8S*09!VBzrCThHBRHj,cK!y5y~jP'&XKpxptXZf.Q.ZE9=uf6Zspj!gR(w(!VA;!4a~)&u~!FZJ:llkRtpode;YdzlMeC6Qf0M-9QWBN($+ze6L'fO~WMlNF8~K;&xUQNCv;=7X6KWQ+4t~X7w~zQY3~;GjjEXmT3:JcNsBMY,VQ6YT8tVKS7fy(6IuWpo&+v2)!NNQ8an:a$p;P!f(5(aBO~*pEYOEKM,IcPlTcAqOjk,Q34~QNgN_$WIz'aew3:0ke*'5;suXnY5OJ.OgRSMoiVaPQU65e2vLicg,PdnsDrSdWqgD.Q4*!h2R=MUT$:hu62Rk5xI5p)Zlln!X'yYVbvcYU*T+3@$o_sN76c$U)~*4O.AH,qZeKDTBtCBgr5~-qk~RGHR2RVfyUZ3L8Xr*1fYwW4B60f8~DUe0aA_eKl6s2rUAPgS;A,--qq,)d.@=_22~ZObR9cMrf@ie4G_.YJs.&!UQnb*$nwS)F(U9K+FTLHZ9Moi(xk6sNU+0R$Jps0C6Y's&pOt(Ba)*ZHZ6Ps@n3jp7,A-6GKmHpps~t2!pxwg8YSo43tf-ZnK9oGXYV4,,VsZcgm1E7*X;&(;hZ.edcOZePT456g0Z(j4V$Z,x3S+JAP+cjtQ$e66By5Wbtfc6GPF'nFTpeo2k!tajCwGi,S-sjK8pjR5tIZU=c8$t1svWXuI~*vrtP.*_:v;XSl3sRh~JUL=hQLKJLp6dc0U7FA))UXog8Bs;C~_1Zy@06hemHTd;8GCxM40bCM50:ea4GcnJ$v'q;X4@SM,QC5EG;WiP+1i:YpnOum36zsZ7KT$d'x0cKxx2LytyTwE:'+CRg+=;BRg5=zy209+ek))yxdnO4YAB=8FrYAzPxK*)1xA:)b4IgIj7g,nM2k;l4LR:fPI*,!ZXgYey~kMg-Hf.=N*2SPrO4_axcRq!JJw05mwR8)ikGV*b2u6U-;jYqEZ~Vk!wwewYo-4DUbR08GWh6ne+oI9b1z1H',FwV_xCjD,zs9v2JGYL3H.C)08l$.CX,AXHKr1v=C_tq,+VN3jn-s9JjqRC+5S!-;igIgd@NmePOl8J,T.IJ&ggNbkD&1BXMOxfo&J$3f'2JR'Je;Lph2aX~8KybXvMo~nB(&ZTazU0iz8QpOBxl`;
            const res1 = await chai.request(`http://localhost:${portMurmurHashInt}`).post('/shorten').send({ longURL: url });
            const res2 = await chai.request(`http://localhost:${portMurmurHashInt}`).post('/shorten').send({ longURL: url2 });
            expect(res1.body.shortURL).to.not.equal(res2.body.shortURL);
        });
    });
});
