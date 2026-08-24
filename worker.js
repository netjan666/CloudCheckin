export default {
    async fetch(request, env, ctx) {
      const url = new URL(request.url);
      
      if (url.pathname === '/test') {
        try {
          const response = await fetch(env.CIRCLECI_WEBHOOK_URL, {
            method: 'POST',
            headers: {
              'Circle-Token': env.CIRCLECI_TOKEN,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ branch: 'main' }),
          });
          
          const responseText = await response.text();
          return new Response(`Test completed. Status: ${response.status}\nResponse: ${responseText}`, {
            status: 200,
            headers: { 'Content-Type': 'text/plain' }
          });
        } catch (error) {
          return new Response(`Test failed: ${error.message}`, { 
            status: 500,
            headers: { 'Content-Type': 'text/plain' }
          });
        }
      }
      
      return new Response('CircleCI Scheduler Worker is running', { 
        status: 200,
        headers: { 'Content-Type': 'text/plain' }
      });
    },
  
    async scheduled(event, env, ctx) {
      try {
        const response = await fetch(env.CIRCLECI_WEBHOOK_URL, {
          method: 'POST',
          headers: {
            'Circle-Token': env.CIRCLECI_TOKEN,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ branch: 'main' }),
        });
        
        const timestamp = new Date().toISOString();
        console.log(`[${timestamp}] Scheduled request executed`);
        console.log(`Response status: ${response.status}`);
        
        const result = await response.text();
        console.log('Response body:', result);
        
      } catch (error) {
        console.error('Scheduled request failed:', error);
      }
    }
};